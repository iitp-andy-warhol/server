# con_db.py 사용법
python con_db.py [exp_id] [command] [orderid]

DB orders 테이블 조회
일부칼럼 조회
python con_db.py exp_id s

전체칼럼 조회
python con_db.py exp_id sa

특정 order 조회(eg. order_id=87)
python con_db.py exp_id s 87
python con_db.py exp_id sa 87


DB orders 테이블 행 삭제
전체 order 삭제
python con_db.py exp_id d

특정 order 삭제
python con_db.py exp_id d

