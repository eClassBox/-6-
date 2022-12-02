import re
import csv
import pandas as pd
import sys, time, datetime, pyupbit  # Window의 System을 접근하는 모듈을 불러옵니다.
import pandas as pd
from PyQt5.QtWidgets import *  # PyQt5의 기본적인 UI를 구성하는 모듈을 불러옵니다.
from PyQt5 import QtGui, uic  # 해당 UI를 불러옵니다.
from PyQt5.QtCore import *
from pyqtgraph import *
import finplot as fplt

fplt.display_timezone = datetime.timezone.utc
fplt.candle_bull_color = "#FF0000"
fplt.candle_bull_body_color = "#FF0000"
fplt.candle_bear_color = "#0000FF"

# UI파일 연결
# 단, UI파일은 Python 코드 파일과 같은 디렉토리에 위치해야한다
tickers = ["KRW-BTC", "KRW-ADA", "KRW-XRP", "KRW-DOGE", "KRW-ETH"]
form_class = uic.loadUiType("main.ui")[0]


class Worker(QThread):
    # 사용자 정의 시그널 특정 이벤트가 발생 했을 시 이 시그널 방출
    timeout = pyqtSignal(pd.DataFrame)
    coinDataSent = pyqtSignal(int)

    def __init__(self, *args):
        super().__init__(*args)
        self.woriking = True

    def get_ohlcv(self):
        # get_ohlcv 함수는 고가/시가/저가/종가/거래량을 DataFrame으로 반환합니다.
        self.df = pyupbit.get_ohlcv(ticker="KRW-BTC", interval="minute1")
        self.df = self.df[['open', 'high', 'low', 'close']]
        # 시가, 고가, 저가, 종가 순
        self.df.columns = ['Open', 'High', 'Low', 'Close']

    # self.CurrentPrice3 = CurrentPrice3

    def run(self):  # 1분봉 데이터
        self.get_ohlcv()

        while True:
            # get_current_price 함수는 암호화폐의 현재가를 얻어옵니다. 함수로 티커를 넣어줘야 합니다. 티커 : 한줄씩 정보 출력
            # verbose = True : 상세한 정보 표준 출력으로 자세히 나타낼 것인가
            data3 = pyupbit.get_current_price("KRW-BTC", verbose=True)
            # tride_price : 거래가 만 price3에 삽입
            price3 = data3['trade_price']
            # 시간 설정
            # 타임스태프 = 유닉스시간 : 거래 타임스탬프를 1000으로 나눈 값
            time_stamp = data3['trade_timestamp'] / 1000
            # 현재 시각은
            cur_min_time_stamp = time_stamp - time_stamp % (60)
            # 유닉스 타임스탬프로 이루어진 거래시각을 현재시각으로 변환
            cur_min_dt = datetime.datetime.fromtimestamp(cur_min_time_stamp)

            # 현재 거래시각이 가장 최근이면
            if cur_min_dt > self.df.index[-1]:
                # ohlc 데이터프레임 반환
                self.get_ohlcv()
            # 아니라면 거래가 종료된 것이므로
            else:
                # 마지막 캔들 update
                # 최신 이전의 거래시각은 거래 시장이 닫힌 것이므로 close
                self.df.iloc[-1]['Close'] = price3
                if price3 > self.df.iloc[-1]['High']:  # 종가보다 크면 High로 update
                    self.df.iloc[-1]['High'] = price3
                if price3 < self.df.iloc[-1]['High']:  # 종가보다 작으면 Low로 업데이트
                    self.df.iloc[-1]['Low'] = price3

            # 계속해서 최신정보의 현재가 출력
            CurrentPrice3 = pyupbit.get_current_price("KRW-BTC")

            # Worker 메서드 실행시 df 방출
            self.timeout.emit(self.df)
            self.coinDataSent.emit(int(CurrentPrice3))
            # 쿨타임 1초
            time.sleep(1)


# 화면을 띄우는데 사용되는 Class 선언
class WindowClass(QMainWindow, form_class):
    def __init__(self, *args, **kwargs):
        super().__init__()
        self.args = args
        self.setupUi(self)
        self.InitUI(self)
        self.setWindowIcon(QtGui.QIcon('BITUK2.png'))
        self.output.clicked.connect(self.selectedcombo)
        self.buy.clicked.connect(self.pushBuyButton)
        self.sell.clicked.connect(self.pushSellButton)
        self.sell_count.setMaximum(int(self.args[2]))
        # self.output_2.clicked.connect(self.search)

        # self.spinbox.valueChanged.connect(self.changespinbox)
        # self.window = MyWindow()

        # dataframe과 plot 초기화
        self.df = None
        self.plot = None

        self.w = Worker()
        # 사용자 정의 시그널 연결
        self.w.timeout.connect(self.update_data)
        self.w.coinDataSent.connect(self.fillCoindata)
        self.w.start()
        # self.w.coinDataSent.connect(self.changespinbox)

        # self.w2.coinDataSent.connect(self.fillCoindata)
        # self.w.coinDataSent.connect(self.changespinbox)

        # QTimer : PyQt에서 시간의 경과를 체크할 수 있는 객체
        self.timer = QTimer(self)
        self.timer.start(1000)  # 현재 시간 1000ms(밀리초)
        # 사용자 정의 시그널 연결
        self.timer.timeout.connect(self.update)
        # self.timer.timeout.connect(self.update2)

        # finplot 생성(확대가 가능한)
        self.ax = fplt.create_plot(init_zoom_periods=100)
        self.axs = [self.ax]

        # 그리드 레이아웃에 위젯추가(범위를 socket형식 TCP 서버 할당방법으로 불러옴)
        self.gridLayout_Bit.addWidget(self.ax.vb.win, 0, 0)
        # self.gridLayout_ADA.addWidget(self.ax.vb.win, 0, 0)
        # 창의 이름
        # self.gridLayout_ADA.addWidget(self.bx.vb.win, 0, 0)
        # self.setWindowTitle('Real Time Chart - XRP')

    def update(self):
        # 데이터프레임이 존재하지 않는다면 = 최신
        if self.df is not None:
            # 그래프도 존재하지 않으면 = 처음
            if self.plot is None:
                # 데이터프레임을 바탕으로 그래프 제작
                self.plot = fplt.candlestick_ochl(self.df[['Open', 'Close', 'High', 'Low']])
                # finplot 그래프 출력(고정 해제)
                fplt.show(qt_exec=False)
            else:
                # 그래프 존재하면 = 업데이트 필요
                self.plot.update_data(self.df[['Open', 'Close', 'High', 'Low']])

    @pyqtSlot(pd.DataFrame)  # override plot으로 이미 넘어간 후 다음 dataframe을 할당할 함수
    def update_data(self, df):
        self.df = df

    def pushBuyButton(self):
        if int(self.user_money.text()) > int(self.buy_price.text()):
            self.user_money.setText(str(int(self.user_money.text()) - int(self.buy_price.text())))
            self.bitcoin.setText(str(int(self.bitcoin.text()) + int(self.buy_count.value())))
        else:
            self.buyActivateMessage()

    def pushSellButton(self):
        if int(self.bitcoin.text()) != 0:
            self.bitcoin.setText(str(int(self.bitcoin.text()) - int(self.sell_count.value())))
            self.user_money.setText(str(int(self.user_money.text()) + int(self.sell_price.text())))
        else:
            self.SellActivateMessage()

    def buyActivateMessage(self):
        QtWidgets.QMessageBox.information(self, "거래 오류", "보유하고 있는 금액이 너무 적습니다.")

    def SellActivateMessage(self):
        QtWidgets.QMessageBox.information(self, "거래 오류", "보유한 종목이 없습니다.")

    def plot(self, hour, temperature):
        self.graph.plot(hour, temperature)

    def selectedcombo(self):
        if self.combo.currentIndex() == 0:
            # ssss_2의 출력 연습
            # spinbox 최대값 조정
            self.sell_count.setMaximum(int(self.args[2]))

        elif self.combo.currentIndex() == 1:
            self.sell_count.setMaximum(int(self.args[3]))  # fnc_btn_0 호출

        elif self.combo.currentIndex() == 2:
            self.sell_count.setMaximum(int(self.args[4]))

        elif self.combo.currentIndex() == 3:
            self.sell_count.setMaximum(int(self.args[5]))

        elif self.combo.currentIndex() == 4:
            self.sell_count.setMaximum(int(self.args[6]))

    # 현재가 출력
    def fillCoindata(self, CurruntPrice3):
        self.now_cur.setText(f"{CurruntPrice3:,.0f}원")
        self.buy_price.setText(str(self.buy_count.value() * CurruntPrice3))
        self.sell_price.setText(str(self.sell_count.value() * CurruntPrice3))

    # 각 qlabel 값 초기화
    def InitUI(self, *args):
        self.hello.setText("환영합니다 %s님" % self.args[0])  # user_id 인사 출력
        self.user_name.setText(" %s" % self.args[0])  # user_id 출력
        self.user_money.setText(self.args[1])  # user_money 출력
        self.bitcoin.setText(self.args[2])  # 비트코인 보유 개수 출력
        self.ripple.setText(self.args[3])  # 리플 보유 개수 출력
        self.ada.setText(self.args[4])  # ADA 보유 개수 출력
        self.doggie.setText(self.args[5])  # 도지 보유 개수 출력
        self.eth.setText(self.args[6])  # ETH 보유 개수 출력
        self.statusBar()  # 상태바 제작
        # 상태바 메세지와 빨간 색깔과 1 굵기 출력
        self.statusBar().showMessage("사용자의 매수 매도에 따른 결과는 프로그램이 책임져 주지 않습니다.")
        # 현재시각을 상태바에 출력
        # now = datetime.datetime.now()
        # 현재시각을 상태바에 출력
        # self.statusBar().showMessage(str(now))
        self.statusBar().setStyleSheet('border : 1; color : red;')
        # self.now_cur.setText(self.Worker.CurrentPrice3))

    def quit(self):
        self.w.stop()

    def closeEvent(self, QCloseEvent):
        re = QMessageBox.question(self, "종료 확인", "종료 하시겠습니까?",
                                  QMessageBox.Yes | QMessageBox.No)

        if re == QMessageBox.Yes:
            QCloseEvent.accept()
            QFileDialog.getSaveFileName(self, 'Save File', './')

        else:
            QCloseEvent.ignore()


# csv 파일 실행 연습


# pandas DataFrame 연습
df = pd.read_csv('data.csv', encoding='cp949')

while True:
    menu = input("------------------\n1. 회원가입\n2. 로그인\n3. 회원탈퇴\n4. 프로그램 종료\n-----------------\n메뉴 입력 : ")

    # 회원가입 옵션
    if menu == '1':
        # load_file()
        # l = load_file().load
        s = open("data.csv")
        data = csv.reader(s)
        header = next(data)
        lines = s.readlines()
        line_com = []
        trash = []
        id_com = []
        mn_com = []
        pw_com = []
        for line in lines:
            line_com.append(line)  # 정보가 들어있는 텍스트 파일을 한 줄씩 분리해 저장

        for i in range(len(line_com)):
            trash = line_com[i].split(",")  # 한 줄로 되어있는 리스트 요소를 공백문자로 나누고 쓰레기 리스트에 저장
            id_com.append(trash[0])  # 쓰레기 리스트의 첫 요소는 ID
            pw_com.append(trash[1])
            mn_com.append(trash[2])
            del trash[7]  # 쓰레기 비우기

        id = input("추가 ID 입력 : ")
        if id in id_com:  # id_com

            print("이미 존재하는 ID 입니다.")
            continue
        else:
            print("ID 생성 완료")

        flag = 0
        while True:
            pw = input("추가 pw 입력 : ")
            if (len(pw) < 8):
                flag = -1
                print("비밀번호가 너무 짧습니다.")
            elif not re.search("[a-zA-Z]", pw):
                flag = -1
                print("적어도 하나의 영문자가 필요")
            elif not re.search("[0-9]", pw):
                flag = -1
                print("적어도 하나의 숫자가 필요")
            else:
                flag = 0
                print("유효한 비밀번호")
                break
            if flag == -1:
                print("유효한 비밀번호가 아닙니다.")
                continue

        while True:
            mn = input("money 입력 : ")
            if mn.isdigit() == False:
                print("올바른 정수값이 아닙니다. 다시 입력하세요.")
            else:
                print("금액 저장")
                break
        new_arr = {'ID': [id], 'PW': [pw], 'Money': [mn], 'A': [0], 'B': [0], 'C': [0], 'D': [0], 'E': [0]}
        # df=df.append(pd.Series(new_arr,index=['ID','PW','Money','A','B','C','D','E']),ignore_index=True)
        df = pd.concat([df, pd.DataFrame(new_arr)], ignore_index=True)
        df.to_csv('data.csv', index=False)
    # s.close()

    elif menu == '2':

        s = open("data.csv")
        data = csv.reader(s)
        header = next(data)
        lines = s.readlines()
        line_com = []
        trash = []
        id_com = []
        mn_com = []
        pw_com = []
        bit_com = []
        rip_com = []
        ada_com = []
        dog_com = []
        eth_com = []

        for line in lines:
            line_com.append(line)  # 정보가 들어있는 텍스트 파일을 한 줄씩 분리해 저장

        for i in range(len(line_com)):
            trash = line_com[i].split(",")  # 한 줄로 되어있는 리스트 요소를 공백문자로 나누고 쓰레기 리스트에 저장
            id_com.append(trash[0])  # 쓰레기 리스트의 0번 째 요소는 ID
            pw_com.append(trash[1])  # 쓰레기 리스트의 1번 째 요소는 PW
            mn_com.append(trash[2])  # 쓰레기 리스트의 2번 째 요소는 MN
            bit_com.append(trash[3]) # 쓰레기 리스트의 3번 째 요소는 bit
            rip_com.append(trash[4]) # 쓰레기 리스트의 4번 째 요소는 rip
            ada_com.append(trash[5]) # 쓰레기 리스트의 5번 째 요소는 ada
            dog_com.append(trash[6]) # 쓰레기 리스트의 6번 째 요소는 dog
            eth_com.append(trash[7]) # 쓰레기 리스트의 7번 째 요소는 eth
            del trash[7]  # 쓰레기 비우기

        id = input("ID 입력 : ")

        if id in id_com:  # id_com
            print("ID 확인")
        else:
            print("없는 ID 입니다")
            continue

        while True:
            pw = input("pw 입력 : ")

            if pw in pw_com:  # pw_com
                if pw_com.index(pw) == id_com.index(id):
                    print("비밀번호 확인")
                    user_id = id
                    user_mn = mn_com[id_com.index(id)]
                    user_bit = bit_com[id_com.index(id)]
                    user_rip = rip_com[id_com.index(id)]
                    user_ada = ada_com[id_com.index(id)]
                    user_dog = dog_com[id_com.index(id)]
                    user_eth = eth_com[id_com.index(id)].rstrip("\n")
                    print("환영합니다! " + user_id + " 님\n현재 " + user_id + " 님께서 소유하신 자본은 " + user_mn + " 원 입니다!")
                    if __name__ == '__main__':
                        app = QApplication(sys.argv)
                        myWindow = WindowClass(user_id, user_mn, user_bit, user_rip, user_ada, user_dog, user_eth)
                        myWindow.show()
                        app.exec_()

                        break
                    break
                else:
                    print("비밀번호가 일치하지 않습니다")
                    break
            else:
                print("비밀번호가 일치하지 않습니다.")
                continue

        # s.close()


    elif menu == '3':
        s = open("data.csv")
        data = csv.reader(s)
        header = next(data)
        lines = s.readlines()
        line_com = []
        trash = []
        id_com = []
        pw_com = []
        for line in lines:
            line_com.append(line)  # 정보가 들어있는 텍스트 파일을 한 줄씩 분리해 저장

        for i in range(len(line_com)):
            trash = line_com[i].split(",")  # 한 줄로 되어있는 리스트 요소를 공백문자로 나누고 쓰레기 리스트에 저장
            id_com.append(trash[0])  # 쓰레기 리스트의 첫 요소는 ID
            pw_com.append(trash[1])
            del trash[7]  # 쓰레기 비우기

        del_id = input("삭제할 ID 입력 : ")
        if del_id not in id_com:
            print("해당 ID가 존재하지 않습니다. ")
        else:
            del_pw = input("삭제할 비밀번호 입력 : ")

            if del_pw in pw_com:

                if pw_com.index(del_pw) == id_com.index(del_id):  # 삭제할 ID와 비밀번호가 맞을경우
                    # d_flag=0
                    while (1):
                        del_answer = input(del_id + " 의 계정을 정말로 삭제합니까? [y/n] : ")
                        if re.search("[yY]", del_answer):
                            renew_df = df.drop(id_com.index(del_id), axis=0)
                            renew_df.to_csv('data.csv', index=False)
                            print("해당 계정이 삭제되었습니다.")
                            break
                        elif re.search("[nN]", del_answer):
                            break

                        else:
                            print("정확한 값을 입력해주세요.")

                else:
                    print("비밀번호가 틀립니다.")

            else:
                i = 1
                print("비밀번호가 틀립니다.")

        s.close()


    elif menu == '4':
        print("프로그램을 종료합니다.")
        exit()