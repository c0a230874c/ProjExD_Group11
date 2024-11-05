import numpy as np
import datetime
import os
import sys
import uuid
import pygame as pg
from pygame.locals import *
from module.kari import Text, event_loop
from random import randint as ran
from typing import List


# 定数宣言部
HEIGHT = 650
WIDTH = 450
RAD =25#こうかとんボールの半径
BALL_X=75#ボールのⅹ距離
BALL_Y=75

# 関数宣言部
def elise(ball_lst: list,judge: list)-> list:
    """
    引数:ball_lst　ボールの色やなしを保持するリスト
    引数:judge判定された
    コンボ判定されたball_lstを0にする
    judge =[[0,1],[0,2]]etc
    """
    for i in judge:
        ball_lst[i[0]][i[1]] =0
    return ball_lst

# クラス宣言部
class KoukatonDrop(pg.sprite.Sprite):
    """
    こうかとんに関するクラス
    """
    color=(
        None,
        (255,0,0),#赤
        (0,0,255),#青
        (0,255,0),#緑
        (255,255,0),#黄
        (136,72,152)#紫
    )
    def __init__(self,ball_list: list[list],num: tuple):
        super().__init__()
        self.kk_img = pg.image.load("fig/3.png")
        self.kk_img = pg.transform.flip(self.kk_img, True, False)
        self.kk_img.fill((255,255,255,128),None, pg.BLEND_RGBA_MULT)
        self.image = pg.Surface((2*RAD, 2*RAD))
        self.i=num[0]
        self.j=num[1]
        self.col =__class__.color[ball_list[self.i][self.j]]
        self.image.set_alpha(128)
        self.image.set_colorkey((0, 0, 0))
        self.rect = self.image.get_rect()
        self.rect.center = self.i*BALL_X+12,self.j*BALL_Y+215
                

    
    def update(self,screen:pg.surface):
        screen.set_alpha(128)
        screen.set_colorkey((0, 0, 0))
        if self.col is not None:
            # コンボして表示しない時を除いて表示する
            pg.draw.circle(screen, self.col, (self.rect.centerx+RAD,self.rect.centery+RAD), RAD)
            screen.blit(self.kk_img, [self.rect.centerx, self.rect.centery])
        self.kill()

class ScoreLogDAO:
    """
    それぞれのスコアデータの入出力を管理するクラス
    TODO: できればデータベース化
    """
    def __init__(self,log_file_name:str = "score_log.csv", file_encoding:str = "utf-8") -> None:
        """
        スコアログを保存する先がなければ作成する
        また、任意のファイル名へと変更できる
        保存先のパスは"./logs"内になる

        :param str log_file_name: ファイル名
        :param str file_encoding: ファイルのエンコード方式
        """
        self.file_encoding = file_encoding
        self.log_file_path = "./logs"

        if not os.path.exists(self.log_file_path):
            # フォルダがなければ作成する
            os.mkdir(self.log_file_path)
        
        self.log_file = self.log_file_path + "/" + log_file_name
        if not os.path.exists(self.log_file):
            # ログファイルがなければ初期化する
            with open(self.log_file, "w", encoding=self.file_encoding) as f:
                f.write("uuid,player_name,score,created_time\n")

        # タイムスタンプ準備
        t_delta = datetime.timedelta(hours=9)
        jts = datetime.timezone(t_delta, 'JST')
        self.now = datetime.datetime.now(jts)
    
    def insert(self, uuid:str, player_name:str, score:int) -> bool:
        """
        プレイログを挿入する

        :param str uuid: UUID
        :param str player_name: プレイヤー名
        :param str score:
        :return: 成功したらTrueを返します
        :rtype: bool
        """
        with open(self.log_file, "a", encoding=self.file_encoding) as f:
            f.write(f"{uuid},{player_name},{score},{self.now.strftime('%Y/%m/%d %H:%M:%S')}\n")

        return True
    
    def get(self)->list[tuple[str,str,int,str]]:
        """
        保存されているプレイログデータを取得します

        :return: ログデータのtupleを返します
        :rtype: tuple[tuple[str,str,int,str]]
        """
        result = []
        with open(self.log_file, "r", encoding=self.file_encoding) as f:
            f.readline()
            result += [self.dismantling(row) for row in f]
        
        return result

    def dismantling(self,row:str)->tuple[str,str,str,str]:
        """
        プレイログデータの一行をそれぞれの要素に分解し、tupleで返します

        :return: uuid, player_name, score, created_time
        :rtype: tuple[str,str,str,str]
        """
        datas = row.rstrip("\n").rsplit(",")

        return tuple(datas)

class Score:
    """
    スコア管理システム
    """
    def __init__(self, session:ScoreLogDAO, player_name:str = "guest"):
        """
        スコアをユーザと紐づけます
        担当 : c0a23019
        
        :param str player_name: プレイヤー名
        """
        self.session = session

        # スコア情報系
        self.value = 0
        self.player_name = player_name
        self.player_uuid = str(uuid.uuid1())
        # TODO: 遊んだ時間のlog取得

        # 表示系
        self.font = pg.font.Font(None, 50)
        self.color = (0, 0, 255)
        self.image = self.font.render(f"Score: {self.value}", 0, self.color)
        self.rect = self.image.get_rect()
        self.rect.center = 100, 100

    def update(self, screen: pg.Surface):
        """
        スコア表示

        :param Surface screen: スクリーン情報
        """
        self.image = self.font.render(f"Score: {self.value}", 0, self.color)
        screen.blit(self.image, self.rect)

    def add(self, add_score:int):
        """
        スコア加算

        :param int add_score: 加算したい値
        """
        self.value += add_score

    def save(self) -> None:
        # TODO: クラス削除時にスコアをファイルに保存する
        self.session.insert(self.player_uuid, self.player_name, self.value)

# クラス宣言部
class PuzzleList():
    """
    パズル画面を管理するリストに関係するクラス
    """

    def __init__(self):
        """
        3つ以上繋げることがないようにする
        """
        self.lis=self.puzzle_generate(6,6)
        

    def puzzle_generate(self,rows:int, cols:int)->np.ndarray:
        array = np.array([[0] * cols for _ in range(rows)])  # 初期化

        for i in range(rows):
            for j in range(cols):
                while True:
                    num = np.random.randint(1, 6)  # 1から5の間のランダムな数
                    # 同じ行または列に3つ連続していないかを確認
                    if (j < 2 or array[i][j-1] != num or array[i][j-2] != num) and \
                    (i < 2 or array[i-1][j] != num or array[i-2][j] != num):
                        array[i][j] = num
                        break

        return array                        

    def get_lis(self):
        return self.lis
    
class Score:
    """
    スコア管理システム
    """
    def __init__(self, player_name:str = "guest"):
        """
        スコアをユーザと紐づけます
        担当 : c0a23019
        
        :param str player_name: プレイヤー名
        """
        # スコア情報系
        self.value = 0
        self.player_name = player_name
        self.player_uuid = uuid.uuid1()
        # TODO: 遊んだ時間のlog取得
        
        # 表示系
        self.font = pg.font.Font(None, 50)
        self.color = (0, 0, 255)
        self.image = self.font.render(f"Score: {self.value}", 0, self.color)
        self.rect = self.image.get_rect()
        self.rect.center = 100, 100

    def update(self, screen: pg.Surface):
        """
        スコア表示

        :param Surface screen: スクリーン情報
        """
        self.image = self.font.render(f"Score: {self.value}", 0, self.color)
        screen.blit(self.image, self.rect)

    def add(self, add_score:int):
        """
        スコア加算

        :param int add_score: 加算したい値
        """
        self.value += add_score

    def save(self) -> None:
        # TODO: クラス削除時にスコアをファイルに保存する
        self.session.insert(self.player_uuid, self.player_name, self.value)


# main関数
def main():
    pg.display.set_caption("はばたけ！こうかとん")
    screen = pg.display.set_mode((WIDTH, HEIGHT))
    clock = pg.time.Clock()

    # 名前入力用のTextインスタンスを作成
    font = pg.font.SysFont("yumincho", 30)
    text = Text()  # Text クラスをインスタンス化
    pg.key.start_text_input()  # テキスト入力を開始

    # 背景画像の読み込み
    bg_img = pg.image.load("C:\\Users\\Admin\\Documents\\ProjExD\\ex5\\fig\\pg_bg.jpg")
    bg_imgs = [bg_img, pg.transform.flip(bg_img, True, False)]
    
    # キャラクター画像の読み込みと設定
    kk_img = pg.image.load("C:\\Users\\Admin\\Documents\\ProjExD\\ex5\\fig\\3.png")
    kk_img = pg.transform.flip(kk_img, True, False)

    # キャラクターの初期座標設定
    kk_rct = kk_img.get_rect()
    kk_rct.center = 300, 200

    score = Score()


    text = Text()

    tmr = 0 # 時間保存

    ball = pg.sprite.Group()
    lis= PuzzleList()
    """
    status変数について
    本変数では画面・実行機能を選択する値を管理します。
    次の状態を代入してあげるだけで簡単に遷移を実現できます
    以下の範囲に基づいて使用してください

    {機能名}:{状態番号}

    例
    ホーム画面に関する機能
    status = "home:0"
    """
    status:str = "home:0"

    while True:
        # 共通処理部
        
        event_list = pg.event.get()

        # 各statusに基づく処理部
        match status:
            case "home:0":
                for event in event_list:
                    if event.type == pg.QUIT: return
                status = "home:1"
            case "home:1":
                for event in pg.event.get():
                    # キーが押されたらゲーム画面へ
                    player_name = event_loop(screen, text, font)  # 名前入力後、イベントループから取得
                    if not player_name:
                        player_name = None
                    print(f"Player Name: {player_name}")
                    status = "game:0"
                    break
            case "game:0":
                    if event.type == pg.KEYDOWN:
                        status = "game:0"
                        break
            
            case "game:0":
                """
                ゲームの初期化
                """
                status = "game:1"
                t = lis.get_lis()
                for i in range(len(t)):
                    for j in range(len(t[i])):
                        ball.add(KoukatonDrop(lis.get_lis(),(i,j)))
                status="game:1"           



            case "game:1":     
                # 練習7
                for i in range(4):
                    screen.blit(bg_imgs[i%2], [-(tmr % 3200)+1600*i, 0])
                for event in pg.event.get():
                    if event.type == pg.QUIT:
                        return

                key_lst = pg.key.get_pressed() # 練習8-3 全キーの押下状態取得
                
                # 練習8-4 方向キーの押下状態を繁栄
                kk_rct_tmp = (
                    key_lst[pg.K_RIGHT] * 2 + key_lst[pg.K_LEFT] * (-1) - 1,
                    key_lst[pg.K_UP] * (-1) + key_lst[pg.K_DOWN] * 1
                    )
                kk_rct.move_ip(kk_rct_tmp)
                

                for i in range(len(t)):
                    for j in range(len(t[i])):
                        ball.add(KoukatonDrop(lis.get_lis(),(i,j)))
                    ball.update(screen)                               
                    ball.draw(screen)
                    
                    lis= PuzzleList()              
                
                score.add(10)
                score.update(screen)

        # 共通処理部
        pg.display.update()
        tmr += 1        
        clock.tick(200)
        print(status)

if __name__ == "__main__":
    pg.init()
    main()
    pg.quit()
    sys.exit()
