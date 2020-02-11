from server import *
from scheduler_utils import *

host = 'localhost'
user = 'root'
passwd = 'pass'
dbname = 'orderdb'
table_name = 'orders'

LOADING_ZONE = 0


def find_least_stop_os(order_list):
    # Sort partial orders so that the addresses w/ most pending items come first
    add_dict = group_same_address(order_list)
    for add, orders in add_dict.items():
        add_dict[add] = sorted(orders, key=lambda x: count_items(x))
    sorted_add = sorted(add_dict.values(), key=lambda x: evaluate_order_set(x))[::-1]
    os_by_add = [group_orders_n(add, BASKET_SIZE) for add in sorted_add]
    grouped_partial_orders = concat_orders(os_by_add)

    single_add = list(filter(lambda x: count_items(x) > OS_MIN, grouped_partial_orders))

    if len(single_add):
        single_add = sorted(single_add, key=lambda x: get_profit(x))[::-1]
        best_os = single_add[0]
    else:
        multiple_add = list(filter(lambda x: count_items(x) <= OS_MIN, grouped_partial_orders))
        partials = concat_orders(multiple_add)
        multiple_add = group_orders_n(partials, BASKET_SIZE)
        multiple_add = sorted(multiple_add, key=lambda x: get_profit(x))[::-1]
        best_os = multiple_add[0]
    return best_os

def Schedule(existing_order_grp_profit,
             order_grp_new,
             order_grp_new_lock,
             update_order_grp_flag,
             update_order_grp_flag_lock,
             pending_df,
             scheduling_required_flag,
             scheduling_required_flag_lock,
             schedule_changed_flag,
             schedule_changed_flag_lock,
             next_orderset_idx,
             next_orderset_idx_lock,
             operating_order_id,
             direction,
             current_address,
             current_basket_r,
             current_basket_g,
             current_basket_b,
             schedule_current_basket_lock,
             operating_dump_id,
             scheduler_id,
             did_scheduling_dumpid):

    print('@@@@@@@@@@@ Schedule() is on@@@@@@@@@@@ ')
    sc_logger = Logger(for_scheduler=True, scheduler_id=scheduler_id.value)
    osID = 0
    dumID = 0

    @timefn
    def get_optimized_order_grp(existing_order_grp_profit, pdf, rs, threshold=0):
        if len(pdf) == 0:
            return None
        pdf['partialid'] = 0
        pdf['profit'] = 1
        pending_orders = [od.makeOrder(row) for idx, row in pdf.iterrows()]

        # Convert to partial orders
        to_loading_zone = rs['operating_order']['id'] in [9999, 99999]
        at_loading_zone = rs['current_address'] == 0
        current_basket = rs['current_basket']

        all_partials = partialize_for_loading(pending_orders, item_limit=PARTIAL_THRESHOLD)
        # Update order profit
        all_partials = [evaluate_order(rs['current_address'], order) for order in all_partials]

        if to_loading_zone or at_loading_zone:
            # Sort orders by profit
            all_partials = filter_empty_orders(all_partials)
            partials_sorted = sort_orders(all_partials, by='profit', ascending=False)
            grouped_partial_orders = group_orders_n(partials_sorted, BASKET_SIZE)
        else:
            in_basket, not_in_basket = partialize_by_rgb(all_partials, current_basket)
            # in_basket = sort_orders(in_basket, by='profit', ascending=False)  # optional
            this_os, remaining_orders = group_orders_for_basket(in_basket, current_basket)
            remaining_orders += not_in_basket

            this_os = filter_empty_orders(this_os)
            remaining_orders = filter_empty_orders(remaining_orders)

            # Sort remaining orders by profit
            remaining_orders = sort_orders(remaining_orders, by='profit', ascending=False)

            # Group partial orders
            grouped_partial_orders = group_orders_n(remaining_orders, BASKET_SIZE)

        # Make dump orders
        nonlocal dumID
        all_dumps = []
        for po_group in grouped_partial_orders:
            group_by_address = group_same_address(po_group).values()
            for dumped_order in group_by_address:
                all_dumps.append(od.makeDumpedOrder(dumpid=dumID, PartialOrderList=dumped_order))
                dumID += 1

        grouped_dumped_orders = group_orders_n(all_dumps, BASKET_SIZE)

        if to_loading_zone or at_loading_zone:
            grouped_dumped_orders = filter_empty_orders(grouped_dumped_orders)
        else:
            this_dump = []
            group_by_address = group_same_address(this_os).values()
            for i, dumped_order in enumerate(group_by_address, 1):
                this_dump.append(od.makeDumpedOrder(dumpid=dumID, PartialOrderList=dumped_order))
                dumID += 1
            if count_items(this_dump) > 0:
                grouped_dumped_orders.insert(0, this_dump)

        nonlocal osID
        # Make order sets
        all_ordersets = [od.makeOrderSet(direction=rs['direction'], current_address=rs['current_address'],
                                         ordersetid=osID, DumpedOrderList=grouped_dumped_orders[0])]
        osID += 1
        for do_group in grouped_dumped_orders[1:]:
            # TODO : improve algorithm estimating profit
            os = od.makeOrderSet(direction=all_ordersets[-1]['last_direction'],
                                 ordersetid=osID, DumpedOrderList=do_group)
            all_ordersets.append(os)
            osID += 1


        # Make order group
        new_order_grp = od.makeOrderGroup(OrderSetList=all_ordersets)

        if new_order_grp['profit'] - existing_order_grp_profit > threshold:
            return new_order_grp
        else:
            return None

    while True:
        if scheduling_required_flag.value:
            print('@@@@@@@@@@@ Making new schedule @@@@@@@@@@@')
            schedule_current_basket_lock.acquire()
            schedule_info = {
                'direction': direction.value,
                'current_address': current_address.value,
                'current_basket': {'r': current_basket_r.value, 'g': current_basket_g.value, 'b': current_basket_b.value},
                'operating_order': {'id':operating_dump_id.value}
            }
            schedule_current_basket_lock.release()

            print("schedule_info: ", schedule_info)

            pdf_for_scheduling = pending_df.df.copy()
            pdf_for_scheduling = pdf_for_scheduling.iloc[
                [x not in operating_order_id.l for x in pdf_for_scheduling['id']]].reset_index()

            pdf_for_scheduling['red'] = pdf_for_scheduling['required_red']
            pdf_for_scheduling['green'] = pdf_for_scheduling['required_green']
            pdf_for_scheduling['blue'] = pdf_for_scheduling['required_blue']
            del pdf_for_scheduling['required_red']
            del pdf_for_scheduling['required_green']
            del pdf_for_scheduling['required_blue']

            sc_logger.scheduling['start_time'] = now()
            if len(pdf_for_scheduling) != 0:
                sc_logger.scheduling['num_order'] = len(pdf_for_scheduling)
            else:
                sc_logger.scheduling['num_order'] = 1

            num_item = 0
            for i in range(len(pdf_for_scheduling)):
                num_item += pdf_for_scheduling[['red', 'green', 'blue']].iloc[i].sum()
            sc_logger.scheduling['num_item'] = num_item

            new_order_grp = get_optimized_order_grp(existing_order_grp_profit.value, pdf_for_scheduling, schedule_info)
            sc_logger.scheduling['end_time'] = now()
            sc_logger.insert_log(sc_logger.scheduling)

            if new_order_grp is not None:

                did_scheduling_dumpid.value = schedule_info['operating_order']['id']
                order_grp_new_lock.acquire()
                order_grp_new['dict'] = new_order_grp
                order_grp_new_lock.release()

                update_order_grp_flag_lock.acquire()
                update_order_grp_flag.value = True
                update_order_grp_flag_lock.release()

                schedule_changed_flag_lock.acquire()
                schedule_changed_flag.value = True
                schedule_changed_flag_lock.release()

                next_orderset_idx_lock.acquire()
                next_orderset_idx.value = -1
                next_orderset_idx_lock.release()

                scheduling_required_flag_lock.acquire()
                scheduling_required_flag.value = False
                scheduling_required_flag_lock.release()

            else:
                scheduling_required_flag_lock.acquire()
                scheduling_required_flag.value = False
                scheduling_required_flag_lock.release()
        time.sleep(0.05)


def ScheduleByAddress(pending_df,
                     update_orderset_flag,
                     update_orderset_flag_lock,
                     scheduling_required_flag,
                     scheduling_required_flag_lock,
                     new_orderset_container,
                     new_orderset_container_lock,
                     direction,
                     free_inventory_r,
                     free_inventory_g,
                     free_inventory_b,
                     scheduler_id):

    print('@@@@@@@@@@@ Schedule() is on@@@@@@@@@@@ ')
    sc_logger = Logger(for_scheduler=True, scheduler_id=scheduler_id.value)
    osID = 0
    dumID = 0

    @timefn
    def get_optimized_orderset(pdf_for_scheduling, direction, free_inventory):
        if len(pdf_for_scheduling) == 0:
                return None
        pdf_for_scheduling['partialid'] = 0
        pdf_for_scheduling['profit'] = 1
        pending_orders = [od.makeOrder(row) for idx, row in pdf_for_scheduling.iterrows()]

        # Partialize orders first (e.g. enforcing basket max size constraint)
        all_partials = partialize_for_loading(pending_orders, item_limit=PARTIAL_THRESHOLD)

        # Update order profit according to # items
        all_partials = [evaluate_order(LOADING_ZONE, order) for order in all_partials]

        # Partialize orders again to satisfy current inventory status
        in_inventory, not_in_inventory = partialize_by_rgb(all_partials, free_inventory)

        if len(in_inventory):
            best_os = find_least_stop_os(in_inventory)
        else:
            # Have to wait until current order set ends and inventory is replenished
            best_os = find_least_stop_os(not_in_inventory)

        nonlocal dumID
        all_dumps = []
        best_os = group_same_address(best_os).values()
        for dumped_order in best_os:
            all_dumps.append(od.makeDumpedOrder(dumpid=dumID, PartialOrderList=dumped_order))
            dumID += 1

        all_dumps = filter_empty_orders(all_dumps)

        nonlocal osID
        # Make order sets
        # TODO : use last direction from previous order set
        next_orderset = od.makeOrderSet(direction=direction,
                                        current_address=LOADING_ZONE,
                                        ordersetid=osID,
                                        DumpedOrderList=all_dumps)
        osID += 1
        return next_orderset

    while True:
        if scheduling_required_flag.value:
            print('@@@@@@@@@@@ Making new schedule @@@@@@@@@@@')

            pdf_for_scheduling = pending_df.df.copy()

            pdf_for_scheduling['red'] = pdf_for_scheduling['required_red']
            pdf_for_scheduling['green'] = pdf_for_scheduling['required_green']
            pdf_for_scheduling['blue'] = pdf_for_scheduling['required_blue']
            del pdf_for_scheduling['required_red']
            del pdf_for_scheduling['required_green']
            del pdf_for_scheduling['required_blue']

            print("*"*50)
            print("PDF FOR SCHEDULING")
            print(pdf_for_scheduling)

            sc_logger.scheduling['start_time'] = now()
            if len(pdf_for_scheduling) != 0:
                sc_logger.scheduling['num_order'] = len(pdf_for_scheduling)
            else:
                sc_logger.scheduling['num_order'] = 0

            num_item = 0
            for i in range(len(pdf_for_scheduling)):
                num_item += pdf_for_scheduling[['red', 'green', 'blue']].iloc[i].sum()
            sc_logger.scheduling['num_item'] = num_item

            free_inventory = {'r': free_inventory_r.value,
                              'g': free_inventory_g.value,
                              'b': free_inventory_b.value}
            new_orderset = get_optimized_orderset(pdf_for_scheduling, direction.value, free_inventory)
            sc_logger.scheduling['end_time'] = now()
            sc_logger.insert_log(sc_logger.scheduling)

            if new_orderset is not None:
                new_orderset_container_lock.acquire()
                new_orderset_container['dict'] = new_orderset
                new_orderset_container_lock.release()

                update_orderset_flag_lock.acquire()
                update_orderset_flag.value = True
                update_orderset_flag_lock.release()

                scheduling_required_flag_lock.acquire()
                scheduling_required_flag.value = False
                scheduling_required_flag_lock.release()

            else:
                scheduling_required_flag_lock.acquire()
                scheduling_required_flag.value = False
                scheduling_required_flag_lock.release()

        time.sleep(0.05)


if __name__ == "__main__":
    pending_df = get_pending()
    pending_df['partialid'] = 0
    pending_df['profit'] = 1
    pending_orders = [dict(row) for idx, row in pending_df.iterrows()]

    # Convert to partial orders
    no_split = list(filter(lambda x: x['item'] <= PARTIAL_THRESHOLD, pending_orders))

    need_split = list(filter(lambda x: x['item'] > PARTIAL_THRESHOLD, pending_orders))
    splitted_orders = [partialize_n(order, PARTIAL_THRESHOLD) for order in need_split]
    splitted_orders = concat_orders(splitted_orders)

    # Update order profits
    curr_location = 0
    pending_partial_orders = no_split + splitted_orders
    pending_partial_orders = [evaluate_order(curr_location, order) for order in pending_partial_orders]

    # Sort orders by profit
    orders_sorted = sort_orders(pending_partial_orders)

    # Group orders to order sets
    order_group = group_orders_n(orders_sorted, BASKET_SIZE)

    # Sort order sets by profit
    order_group_sorted = sort_order_sets(order_group)

    # for order_set in order_group_sorted:
    #     print(f"Number of orders in order set: {len(order_set)} | Number of items: {count_items(order_set)} | Profit: {evaluate_order_set(order_set):.3f}")
