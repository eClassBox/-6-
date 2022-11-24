#from example4 import *
import sys, time, datetime, pyupbit
import pandas as pd
import finplot as fplt
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5 import QtGui, uic
from PyQt5 import QtChart
from pyqtgraph import *
import pyqtgraph as pg


fplt.display_timezone = datetime.timezone.utc
fplt.candle_bull_color = "#FF0000"
fplt.candle_bull_body_color = "#FF0000"
fplt.candle_bear_color = "#0000FF"

form_class = uic.loadUiType("untitled.ui")[0]

class Worker(QThread):

    #사용자 정의 시그널 특정 이벤트가 발생 했을 시 이 시그널 방출
    timeout = pyqtSignal(pd.DataFrame)

    def __init__(self):
        super().__init__()

    def get_ohlcv(self):
        # get_ohlcv 함수는 고가/시가/저가/종가/거래량을 DataFrame으로 반환합니다.
        self.df = pyupbit.get_ohlcv(ticker="KRW-XRP", interval="minute1")
        self.df = self.df[['open', 'high', 'low', 'close']]
        # 시가, 고가, 저가, 종가 순
        self.df.columns = ['Open', 'High', 'Low', 'Close']

    def run(self):  # 1분봉 데이터
        self.get_ohlcv()

        while True:
            #get_current_price 함수는 암호화폐의 현재가를 얻어옵니다. 함수로 티커를 넣어줘야 합니다. 티커 : 한줄씩 정보 출력
            #verbose = True : 상세한 정보 표준 출력으로 자세히 나타낼 것인가
            data3 = pyupbit.get_current_price("KRW-XRP", verbose=True)
            #tride_price : 거래가 만 price3에 삽입
            price3 = data3['trade_price']


            # 시간 설정
            #타임스태프 = 유닉스시간 : 거래 타임스탬프를 1000으로 나눈 값
            time_stamp = data3['trade_timestamp'] / 1000
            #현재 시각은
            cur_min_time_stamp = time_stamp - time_stamp % (60)
            #유닉스 타임스탬프로 이루어진 거래시각을 현재시각으로 변환
            cur_min_dt = datetime.datetime.fromtimestamp(cur_min_time_stamp)

            #현재 거래시각이 가장 최근이면
            if cur_min_dt > self.df.index[-1]:
                # ohlc 데이터프레임 반환
                self.get_ohlcv()
            #아니라면 거래가 종료된 것이므로
            else:
                # 마지막 캔들 update
                # 최신 이전의 거래시각은 거래 시장이 닫힌 것이므로 close
                self.df.iloc[-1]['Close'] = price3
                if price3 > self.df.iloc[-1]['High']:  # 종가보다 크면 High로 update
                    self.df.iloc[-1]['High'] = price3
                if price3 < self.df.iloc[-1]['High']:  # 종가보다 작으면 Low로 업데이트
                    self.df.iloc[-1]['Low'] = price3

            #계속해서 최신정보의 현재가 출력
            CurrentPrice3 = pyupbit.get_current_price("KRW-XRP")
            print(CurrentPrice3)

            # Worker 메서드 실행시 df 방출
            self.timeout.emit(self.df)
            #쿨타임 1초
            time.sleep(1)
    def output(self, CurrentPirce3):
        self.CurrentPrice3 = CurrentPrice3

class xrpGraph(QWidget, form_class) :
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.w = Worker()
        # 사용자 정의 시그널 연결
        self.w.timeout.connect(self.update_data)
        self.w.start()

        # QTimer : PyQt에서 시간의 경과를 체크할 수 있는 객체
        self.timer = QTimer(self)
        self.timer.start(1000)  # 현재 시간 1000ms(밀리초)
        # 사용자 정의 시그널 연결
        self.timer.timeout.connect(self.update)

        # https://wikidocs.net/164461
        # 그래픽 시각화 객체 생성
        # view = QGraphicsView()
        # 그리드레이아웃으로 그래픽 시각화하는 객체 생성
        # grid_layout = QGridLayout(view)
        # setCentralWidget을 통해 위젯이 QMainWindow 전체 차지
        # self.setCentralWidget(view)
        # 그래픽 사이즈
        # self.resize(1200, 600)  # 업비트 사이즈임

        # finplot 생성(확대가 가능한)
        self.ax = fplt.create_plot(init_zoom_periods=100)
        self.axs = [self.ax]

        # 그리드 레이아웃에 위젯추가(범위를 socket형식 TCP 서버 할당방법으로 불러옴)
        self.gridLayout_2.addWidget(self.ax.vb.win, 0, 0)
        # 창의 이름
        # self.setWindowTitle('Real Time Chart - XRP')


def update(self):
    # now = 현재시각
    # now = datetime.datetime.now()
    # 현재시각을 상태바에 출력
    # self.statusBar().showMessage(str(now))

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

#화면을 띄우는데 사용되는 Class 선언
class WindowClass(QMainWindow, form_class) :
    def __init__(self, *args) :
        super().__init__()
        self.args = args
        self.setupUi(self)
        self.InitUI(self)
        self.setWindowIcon(QtGui.QIcon('BITUK2.png'))

        self.output.clicked.connect(self.buttonFunction)
        self.output.clicked.connect(self.selectedcombo)

        self.spinbox.valueChanged.connect(self.changespinbox)
        #self.window = MyWindow()

        # dataframe과 plot 초기화
        self.df = None
        self.plot = None
    def buttonFunction(self):
        one_text = self.combo.currentText()
        self.ssss.setText(one_text+"출력")

    def plot(self, hour, temperature):
        self.graph.plot(hour, temperature)

    def selectedcombo(self,*args):
        if self.combo.currentIndex() == 0:
            #ssss_2의 출력 연습
            self.ssss_2.setText(self.args[2])
            #spinbox 최대값 조정
            self.spinbox.setMaximum(int(self.args[2]))
            xrpGraph().show()

        elif self.combo.currentIndex() == 1:
            self.ssss_2.setText(self.args[3])
            self.spinbox.setMaximum(int(self.args[3]))

        elif self.combo.currentIndex() == 2:
            self.ssss_2.setText(self.args[4])
            self.spinbox.setMaximum(int(self.args[4]))
        elif self.combo.currentIndex() == 3:
            self.ssss_2.setText(self.args[5])
            self.spinbox.setMaximum(int(self.args[5]))
        elif self.combo.currentIndex() == 4:
            self.ssss_2.setText(self.args[6])
            self.spinbox.setMaximum(int(self.args[6]))

   # def sellbtnfunction(self):


    def changespinbox(self):
        self.price.setText(str(self.spinbox.value())+"*"+"10000 = "+str(self.spinbox.value()*10000))

#각 qlabel 값 초기화
    def InitUI(self, *args):
        self.hello.setText("Hello. %s"%self.args[0])            #user_id 인사 출력
        self.user_name.setText(" %s"%self.args[0])              #user_id 출력
        self.user_money.setText(self.args[1])                   #user_money 출력
        self.bitcoin.setText(self.args[2])                      #비트코인 보유 개수 출력
        self.ripple.setText(self.args[3])                       #리플 보유 개수 출력
        self.ada.setText(self.args[4])                          #ADA 보유 개수 출력
        self.doggie.setText(self.args[5])                       #도지 보유 개수 출력
        self.eth.setText(self.args[6])                          #ETH 보유 개수 출력
        self.statusBar()                                        #상태바 제작
        #상태바 메세지와 빨간 색깔과 1 굵기 출력
        self.statusBar().showMessage("사용자의 매수 매도에 따른 결과는 프로그램이 책임져 주지 않습니다.")
        # 현재시각을 상태바에 출력
        # now = datetime.datetime.now()
        # 현재시각을 상태바에 출력
        # self.statusBar().showMessage(str(now))
        self.statusBar().setStyleSheet('border : 1; color : red;')
        #self.now_cur.setText(self.Worker.CurrentPrice3)
        self.now_cur.setText("10000")





if __name__ == "__main__" :

    app = QApplication(sys.argv)
    myWindow = WindowClass("JHY","100000", "4", "5", "3", "6",  "4")
    myWindow.show()
    app.exec_()

