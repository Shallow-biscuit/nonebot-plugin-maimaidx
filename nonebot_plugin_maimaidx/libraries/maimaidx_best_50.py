import math
import traceback
from io import BytesIO
from typing import Tuple, Union, overload

from nonebot.adapters.onebot.v11 import MessageSegment
from PIL import Image, ImageDraw

from ..config import *
from .image import DrawText, image_to_base64, music_picture
from .maimaidx_api_data import maiApi
from .maimaidx_error import *
from .maimaidx_model import ChartInfo, PlayInfoDefault, PlayInfoDev, UserInfo
from .maimaidx_music import mai


class ScoreBaseImage:
    
    _diff = [
        Image.open(maimaidir / 'b50_score_basic.png'), 
        Image.open(maimaidir / 'b50_score_advanced.png'), 
        Image.open(maimaidir / 'b50_score_expert.png'), 
        Image.open(maimaidir / 'b50_score_master.png'), 
        Image.open(maimaidir / 'b50_score_remaster.png')
    ]
    _rise = [
        Image.open(maimaidir / 'rise_score_basic.png'),
        Image.open(maimaidir / 'rise_score_advanced.png'),
        Image.open(maimaidir / 'rise_score_expert.png'),
        Image.open(maimaidir / 'rise_score_master.png'),
        Image.open(maimaidir / 'rise_score_remaster.png')
    ]
    text_color = (255, 255, 255, 255)
    t_color = [
        (255, 255, 255, 255), 
        (255, 255, 255, 255), 
        (255, 255, 255, 255), 
        (255, 255, 255, 255), 
        (138, 0, 226, 255)
    ]
    id_color = [
        (129, 217, 85, 255), 
        (245, 189, 21, 255),  
        (255, 129, 141, 255), 
        (159, 81, 220, 255),
        (138, 115, 226, 255)
    ]
    bg_color = [
        (111, 212, 61, 255), 
        (248, 183, 9, 255), 
        (255, 129, 141, 255), 
        (159, 81, 220, 255), 
        (219, 170, 255, 255)
    ]
    id_diff = [Image.new('RGBA', (55, 10), color) for color in bg_color]
    
    title_bg = Image.open(maimaidir / 'title.png')
    title_lengthen_bg = Image.open(maimaidir / 'title-lengthen.png')
    design_bg = Image.open(maimaidir / 'design.png')
    aurora_bg = Image.open(maimaidir / 'aurora.png').convert('RGBA').resize((1400, 220))
    shines_bg = Image.open(maimaidir / 'bg_shines.png').convert('RGBA')
    pattern_bg = Image.open(maimaidir / 'pattern.png')
    rainbow_bg = Image.open(maimaidir / 'rainbow.png').convert('RGBA')
    rainbow_bottom_bg = Image.open(maimaidir / 'rainbow_bottom.png').convert('RGBA').resize((1200, 200))
    
    def __init__(self, image: Image.Image = None) -> None:
        self._im = image
        dr = ImageDraw.Draw(self._im)
        self._sy = DrawText(dr, SIYUAN)
        self._tb = DrawText(dr, TBFONT)
    
    def whiledraw(
        self, 
        data: Union[List[ChartInfo], List[PlayInfoDefault], List[PlayInfoDev]], 
        dx: bool, 
        height: int = 0
    ) -> None:
        """
        循环绘制成绩
        
        Params:
            `data`: 数据
            `dx`: 是否为新版本成绩
            `height`: 起始高度
        """
        # y为第一排纵向坐标，dy为各行间距
        dy = 170
        if data and type(data[0]) == ChartInfo:
            y = 1700 if dx else 430
        else:
            y = height
        for num, info in enumerate(data):
            if num % 5 == 0:
                x = 70
                y += dy if num != 0 else 0
            else:
                x += 416

            cover = Image.open(music_picture(info.song_id)).resize((135, 135))
            version = Image.open(maimaidir / f'{info.type.upper()}.png').resize((55, 19))
            if info.rate.islower():
                rate = Image.open(maimaidir / f'UI_TTR_Rank_{score_Rank_l[info.rate]}.png').resize((95, 44))
            else:
                rate = Image.open(maimaidir / f'UI_TTR_Rank_{info.rate}.png').resize((95, 44))

            self._im.alpha_composite(self._diff[info.level_index], (x, y))
            self._im.alpha_composite(cover, (x + 5, y + 5))
            self._im.alpha_composite(version, (x + 80, y + 141))
            self._im.alpha_composite(rate, (x + 150, y + 99))
            if info.fc:
                fc = Image.open(maimaidir / f'UI_MSS_MBase_Icon_{fcl[info.fc]}.png').resize((34, 34))
                self._im.alpha_composite(fc, (x + 246, y + 99))
            if info.fs:
                fs = Image.open(maimaidir / f'UI_MSS_MBase_Icon_{fsl[info.fs]}.png').resize((34, 34))
                self._im.alpha_composite(fs, (x + 291, y + 99))
            
            dxscore = sum(mai.total_list.by_id(str(info.song_id)).charts[info.level_index].notes) * 3
            dxnum = dxScore(info.dxScore / dxscore * 100)
            if dxnum:
                self._im.alpha_composite(
                    Image.open(maimaidir / f'UI_GAM_Gauge_DXScoreIcon_0{dxnum}.png').resize((47, 26)), (x + 335, y + 102)
                )

            self._tb.draw(x + 40, y + 148, 20, info.song_id, self.id_color[info.level_index], anchor='mm')
            title = info.title
            if coloumWidth(title) > 18:
                title = changeColumnWidth(title, 17) + '...'
            self._sy.draw(x + 155, y + 20, 20, title, self.t_color[info.level_index], anchor='lm')
            self._tb.draw(x + 155, y + 50, 32, f'{info.achievements:.4f}%', self.t_color[info.level_index], anchor='lm')
            self._tb.draw(x + 338, y + 82, 20, f'{info.dxScore}/{dxscore}', self.t_color[info.level_index], anchor='mm')
            self._tb.draw(x + 155, y + 82, 22, f'{info.ds} -> {info.ra}', self.t_color[info.level_index], anchor='lm')


class DrawBest(ScoreBaseImage):

    def __init__(self, UserInfo: UserInfo, qqid: Optional[Union[int, str]] = None) -> None:
        super().__init__(Image.open(maimaidir / 'b50_bg.png').convert('RGBA'))
        self.userName = UserInfo.nickname
        self.plate = UserInfo.plate
        self.addRating = UserInfo.additional_rating
        self.Rating = UserInfo.rating
        self.sdBest = UserInfo.charts.sd
        self.dxBest = UserInfo.charts.dx
        self.qqid = qqid

    def _findRaPic(self) -> str:
        """
        寻找指定的Rating图片
        
        Returns:
            `str` 返回图片名称
        """
        if self.Rating < 1000:
            num = '01'
        elif self.Rating < 2000:
            num = '02'
        elif self.Rating < 4000:
            num = '03'
        elif self.Rating < 7000:
            num = '04'
        elif self.Rating < 10000:
            num = '05'
        elif self.Rating < 12000:
            num = '06'
        elif self.Rating < 13000:
            num = '07'
        elif self.Rating < 14000:
            num = '08'
        elif self.Rating < 14500:
            num = '09'
        elif self.Rating < 15000:
            num = '10'
        else:
            num = '11'
        return f'UI_CMN_DXRating_{num}.png'

    def _findMatchLevel(self) -> str:
        """
        寻找匹配等级图片
        
        Returns:
            `str` 返回图片名称
        """
        if self.addRating <= 10:
            num = f'{self.addRating:02d}'
        else:
            num = f'{self.addRating + 1:02d}'
        return f'UI_DNM_DaniPlate_{num}.png'

    async def draw(self) -> Image.Image:
        
        logo = Image.open(maimaidir / 'logo.png').resize((404, 161))
        dx_rating = Image.open(maimaidir / self._findRaPic()).resize((300, 59))
        Name = Image.open(maimaidir / 'Name.png')
        MatchLevel = Image.open(maimaidir / self._findMatchLevel()).resize((134, 55))
        ClassLevel = Image.open(maimaidir / 'UI_FBR_Class_00.png').resize((144, 87))
        rating = Image.open(maimaidir / 'UI_CMN_Shougou_Rainbow.png').resize((454, 50))

        self._im.alpha_composite(logo, (5, 130))
        if self.plate:
            plate = Image.open(platedir / f'{self.plate}.png').resize((1420, 230))
        else:
            plate = Image.open(maimaidir / 'UI_Plate_500501.png').resize((1420, 230))
        self._im.alpha_composite(plate, (390, 100))
        icon = Image.open(maimaidir / 'UI_Icon_309503.png').resize((214, 214))
        self._im.alpha_composite(icon, (398, 108))
        if self.qqid:
            try:
                qqLogo = Image.open(BytesIO(await maiApi.qqlogo(qqid=self.qqid)))
                self._im.alpha_composite(qqLogo.convert('RGBA').resize((214, 214)), (398, 108))
            except Exception:
                pass
        self._im.alpha_composite(dx_rating, (620, 122))
        Rating = f'{self.Rating:05d}'
        for n, i in enumerate(Rating):
            self._im.alpha_composite(
                Image.open(maimaidir / f'UI_NUM_Drating_{i}.png').resize((28, 34)), (760 + 23 * n, 137)
            )
        self._im.alpha_composite(Name, (620, 200))
        self._im.alpha_composite(MatchLevel, (935, 205))
        self._im.alpha_composite(ClassLevel, (926, 105))
        self._im.alpha_composite(rating, (620, 275))

        self._sy.draw(635, 220, 30, self.userName, (0, 0, 0, 255), 'lm')
        sdrating, dxrating = sum([_.ra for _ in self.sdBest]), sum([_.ra for _ in self.dxBest])
        self._tb.draw(
            847, 295, 28, 
            f'B35: {sdrating} + B15: {dxrating} = {self.Rating}', 
            (0, 0, 0, 255), 'mm', 3, (255, 255, 255, 255)
        )
        self._sy.draw(
            1200, 2350, 37, 
            f' | Originally Designed by Yuri-YuzuChaN & BlueDeer233 | \n | Prism Plus Designed by Shallow biscuit | Generated by {maiconfig.botName} BOT |', 
            self.text_color, 'mm', 2, (18, 200, 255, 255)
        )

        self.whiledraw(self.sdBest, False)
        self.whiledraw(self.dxBest, True)

        return self._im


def dxScore(dx: int) -> int:
    """
    获取DX评分星星数量
    
    Params:
        `dx`: dx百分比
    Returns:
        `int` 返回星星数量
    """
    if dx <= 85:
        result = 0
    elif dx <= 90:
        result = 1
    elif dx <= 93:
        result = 2
    elif dx <= 95:
        result = 3
    elif dx <= 97:
        result = 4
    else:
        result = 5
    return result


def getCharWidth(o: int) -> int:
    widths = [
        (126, 1), (159, 0), (687, 1), (710, 0), (711, 1), (727, 0), (733, 1), (879, 0), (1154, 1), (1161, 0),
        (4347, 1), (4447, 2), (7467, 1), (7521, 0), (8369, 1), (8426, 0), (9000, 1), (9002, 2), (11021, 1),
        (12350, 2), (12351, 1), (12438, 2), (12442, 0), (19893, 2), (19967, 1), (55203, 2), (63743, 1),
        (64106, 2), (65039, 1), (65059, 0), (65131, 2), (65279, 1), (65376, 2), (65500, 1), (65510, 2),
        (120831, 1), (262141, 2), (1114109, 1),
    ]
    if o == 0xe or o == 0xf:
        return 0
    for num, wid in widths:
        if o <= num:
            return wid
    return 1


def coloumWidth(s: str) -> int:
    res = 0
    for ch in s:
        res += getCharWidth(ord(ch))
    return res


def changeColumnWidth(s: str, len: int) -> str:
    res = 0
    sList = []
    for ch in s:
        res += getCharWidth(ord(ch))
        if res <= len:
            sList.append(ch)
    return ''.join(sList)


@overload
def computeRa(ds: float, achievement: float) -> int:
    """
    计算底分
    
    Params:
        `ds`: 定数
        `achievement`: 成绩
    Returns:
        返回底分
    """
@overload
def computeRa(ds: float, achievement: float, *, onlyrate: bool = False) -> str:
    """
    计算评价
    
    Params:
        `ds`: 定数
        `achievement`: 成绩
        `onlyrate`: 是否只返回评价
    Returns:
        返回评价
    """
@overload
def computeRa(ds: float, achievement: float, *, israte: bool = False) -> Tuple[int, str]:
    """
    计算底分和评价
    
    Params:
        `ds`: 定数
        `achievement`: 成绩
        `israte`: 是否返回所有数据
    Returns:
        (底分, 评价)
    """
def computeRa(
    ds: float, 
    achievement: float, 
    *, 
    onlyrate: bool = False, 
    israte: bool = False
) -> Union[int, Tuple[int, str]]:
    if achievement < 50:
        baseRa = 7.0
        rate = 'D'
    elif achievement < 60:
        baseRa = 8.0
        rate = 'C'
    elif achievement < 70:
        baseRa = 9.6
        rate = 'B'
    elif achievement < 75:
        baseRa = 11.2
        rate = 'BB'
    elif achievement < 80:
        baseRa = 12.0
        rate = 'BBB'
    elif achievement < 90:
        baseRa = 13.6
        rate = 'A'
    elif achievement < 94:
        baseRa = 15.2
        rate = 'AA'
    elif achievement < 97:
        baseRa = 16.8
        rate = 'AAA'
    elif achievement < 98:
        baseRa = 20.0
        rate = 'S'
    elif achievement < 99:
        baseRa = 20.3
        rate = 'Sp'
    elif achievement < 99.5:
        baseRa = 20.8
        rate = 'SS'
    elif achievement < 100:
        baseRa = 21.1
        rate = 'SSp'
    elif achievement < 100.5:
        baseRa = 21.6
        rate = 'SSS'
    else:
        baseRa = 22.4
        rate = 'SSSp'

    if israte:
        data = (math.floor(ds * (min(100.5, achievement) / 100) * baseRa), rate)
    elif onlyrate:
        data = rate
    else:
        data = math.floor(ds * (min(100.5, achievement) / 100) * baseRa)

    return data


async def generate(qqid: Optional[int] = None, username: Optional[str] = None) -> Union[MessageSegment, str]:
    """
    生成b50
    
    Params:
        `qqid`: QQ号
        `username`: 用户名
        `icon`: 头像
    Returns:
        `Union[MessageSegment, str]`
    """
    try:
        if username:
            qqid = None
        userinfo = await maiApi.query_user_b50(qqid=qqid, username=username)
        draw_best = DrawBest(userinfo, qqid)
        
        msg = MessageSegment.image(image_to_base64(await draw_best.draw()))
    except (UserNotFoundError, UserNotExistsError, UserDisabledQueryError) as e:
        msg = str(e)
    except Exception as e:
        log.error(traceback.format_exc())
        msg = f'未知错误：{type(e)}\n请联系Bot管理员'
    return msg