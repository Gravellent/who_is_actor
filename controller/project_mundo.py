import urllib
import json
import pandas as pd
import numpy as np

def get_win_rates():
    cid_map = pd.read_excel('../static/cid_map.xlsx',engine='openpyxl')

    cid_dict = cid_map.set_index('CID')['Champion'].to_dict()

    lane = ['top','jungle','middle','bottom','support']
    v = "1"
    patch = "30"

    df_top = pd.DataFrame(index = cid_dict.values(),columns = cid_dict.values())
    df_top.insert(0,'Champion',cid_dict.values())
    df_top['AVG Win Rate'] = None
    df_jg = pd.DataFrame(index = cid_dict.values(),columns = cid_dict.values())
    df_jg.insert(0,'Champion',cid_dict.values())
    df_jg['AVG Win Rate'] = None
    df_mid = pd.DataFrame(index = cid_dict.values(),columns = cid_dict.values())
    df_mid.insert(0,'Champion',cid_dict.values())
    df_mid['AVG Win Rate'] = None
    df_bot = pd.DataFrame(index = cid_dict.values(),columns = cid_dict.values())
    df_bot.insert(0,'Champion',cid_dict.values())
    df_bot['AVG Win Rate'] = None
    df_sup = pd.DataFrame(index = cid_dict.values(),columns = cid_dict.values())
    df_sup.insert(0,'Champion',cid_dict.values())
    df_sup['AVG Win Rate'] = None

    tm_top = pd.DataFrame(index = cid_dict.values(),columns = cid_dict.values())
    tm_top.insert(0,'Champion',cid_dict.values())
    tm_top['AVG Win Rate'] = None
    tm_jg = pd.DataFrame(index = cid_dict.values(),columns = cid_dict.values())
    tm_jg.insert(0,'Champion',cid_dict.values())
    tm_jg['AVG Win Rate'] = None
    tm_mid = pd.DataFrame(index = cid_dict.values(),columns = cid_dict.values())
    tm_mid.insert(0,'Champion',cid_dict.values())
    tm_mid['AVG Win Rate'] = None
    tm_bot = pd.DataFrame(index = cid_dict.values(),columns = cid_dict.values())
    tm_bot.insert(0,'Champion',cid_dict.values())
    tm_bot['AVG Win Rate'] = None
    tm_sup = pd.DataFrame(index = cid_dict.values(),columns = cid_dict.values())
    tm_sup.insert(0,'Champion',cid_dict.values())
    tm_sup['AVG Win Rate'] = None

    b = 1

    for cid in cid_map['CID']:
        print(b)
        b += 1

        url = "https://axe.lolalytics.com/mega/?ep=champion&p=d&v=" + v + "&patch=" + patch + "&cid=" + str(
            cid) + "&lane=default&tier=gold_plus&queue=420&region=all"
        # print(url)
        req = urllib.request.Request(url, headers={
            'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36"})
        con = urllib.request.urlopen(req)
        encoding = con.info().get_content_charset('utf8')
        data1 = json.loads(con.read().decode(encoding))

        default_lane = data1.get("header").get('defaultLane')
        avg_wr = data1.get("header").get('wr')

        df_top['AVG Win Rate'][cid_dict.get(cid)] = avg_wr
        df_jg['AVG Win Rate'][cid_dict.get(cid)] = avg_wr
        df_mid['AVG Win Rate'][cid_dict.get(cid)] = avg_wr
        df_bot['AVG Win Rate'][cid_dict.get(cid)] = avg_wr
        df_sup['AVG Win Rate'][cid_dict.get(cid)] = avg_wr
        tm_top['AVG Win Rate'][cid_dict.get(cid)] = avg_wr
        tm_jg['AVG Win Rate'][cid_dict.get(cid)] = avg_wr
        tm_mid['AVG Win Rate'][cid_dict.get(cid)] = avg_wr
        tm_bot['AVG Win Rate'][cid_dict.get(cid)] = avg_wr
        tm_sup['AVG Win Rate'][cid_dict.get(cid)] = avg_wr

        url = "https://axe.lolalytics.com/mega/?ep=champion2&p=d&v=" + v + "&patch=" + patch + "&cid=" + str(
            cid) + "&lane=default&tier=gold_plus&queue=420&region=all"
        # print(url)
        req = urllib.request.Request(url, headers={
            'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36"})
        con = urllib.request.urlopen(req)
        encoding = con.info().get_content_charset('utf8')
        data2 = json.loads(con.read().decode(encoding))

        # print(data1.get('enemy_top'))

        for i in range(50):
            # print(data1.get('enemy_top')[i][0])
            win_rate = data1.get('enemy_top')[i][2] / data1.get('enemy_top')[i][1] * 100
            df_top[cid_dict.get(data1.get('enemy_top')[i][0])][cid_dict.get(cid)] = win_rate
        for i in range(45):
            win_rate = data1.get('enemy_jungle')[i][2] / data1.get('enemy_jungle')[i][1] * 100
            df_jg[cid_dict.get(data1.get('enemy_jungle')[i][0])][cid_dict.get(cid)] = win_rate
        for i in range(53):
            win_rate = data1.get('enemy_middle')[i][2] / data1.get('enemy_middle')[i][1] * 100
            df_mid[cid_dict.get(data1.get('enemy_middle')[i][0])][cid_dict.get(cid)] = win_rate
        for i in range(27):
            win_rate = data1.get('enemy_bottom')[i][2] / data1.get('enemy_bottom')[i][1] * 100
            df_bot[cid_dict.get(data1.get('enemy_bottom')[i][0])][cid_dict.get(cid)] = win_rate
        for i in range(36):
            win_rate = data1.get('enemy_support')[i][2] / data1.get('enemy_support')[i][1] * 100
            df_sup[cid_dict.get(data1.get('enemy_support')[i][0])][cid_dict.get(cid)] = win_rate

        # print("check")

        if data2.get('team_top'):
            for i in range(50):
                win_rate = data2.get('team_top')[i][2] / data2.get('team_top')[i][1] * 100
                tm_top[cid_dict.get(data2.get('team_top')[i][0])][cid_dict.get(cid)] = win_rate
        if data2.get('team_jungle'):
            for i in range(45):
                win_rate = data2.get('team_jungle')[i][2] / data2.get('team_jungle')[i][1] * 100
                tm_jg[cid_dict.get(data2.get('team_jungle')[i][0])][cid_dict.get(cid)] = win_rate
        if data2.get('team_middle'):
            for i in range(53):
                win_rate = data2.get('team_middle')[i][2] / data2.get('team_middle')[i][1] * 100
                tm_mid[cid_dict.get(data2.get('team_middle')[i][0])][cid_dict.get(cid)] = win_rate
        if data2.get('team_bottom'):
            for i in range(27):
                win_rate = data2.get('team_bottom')[i][2] / data2.get('team_bottom')[i][1] * 100
                tm_bot[cid_dict.get(data2.get('team_bottom')[i][0])][cid_dict.get(cid)] = win_rate
        if data2.get('team_support'):
            for i in range(36):
                win_rate = data2.get('team_support')[i][2] / data2.get('team_support')[i][1] * 100
                tm_sup[cid_dict.get(data2.get('team_support')[i][0])][cid_dict.get(cid)] = win_rate

        # print("check")

        for ln in lane:
            if ln == default_lane:
                continue

            url = "https://axe.lolalytics.com/mega/?ep=champion&p=d&v=" + v + "&patch=" + patch + "&cid=" + str(
                cid) + "&lane=" + ln + "&tier=gold_plus&queue=420&region=all"
            req = urllib.request.Request(url, headers={
                'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36"})
            con = urllib.request.urlopen(req)
            encoding = con.info().get_content_charset('utf8')
            data1 = json.loads(con.read().decode(encoding))

            if data1.get("header").get('n') <= 50000:
                continue

            print(cid_dict.get(cid))
            print(ln)

            rowname = cid_dict.get(cid) + ' ' + ln

            df_top.loc[rowname] = None
            df_top.loc[rowname][0] = rowname
            df_jg.loc[rowname] = None
            df_jg.loc[rowname][0] = rowname
            df_mid.loc[rowname] = None
            df_mid.loc[rowname][0] = rowname
            df_bot.loc[rowname] = None
            df_bot.loc[rowname][0] = rowname
            df_sup.loc[rowname] = None
            df_sup.loc[rowname][0] = rowname

            tm_top.loc[rowname] = None
            tm_top.loc[rowname][0] = rowname
            tm_jg.loc[rowname] = None
            tm_jg.loc[rowname][0] = rowname
            tm_mid.loc[rowname] = None
            tm_mid.loc[rowname][0] = rowname
            tm_bot.loc[rowname] = None
            tm_bot.loc[rowname][0] = rowname
            tm_sup.loc[rowname] = None
            tm_sup.loc[rowname][0] = rowname

            url = "https://axe.lolalytics.com/mega/?ep=champion2&p=d&v=" + v + "&patch=" + patch + "&cid=" + str(
                cid) + "&lane=" + ln + "&tier=gold_plus&queue=420&region=all"
            req = urllib.request.Request(url, headers={
                'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36"})
            con = urllib.request.urlopen(req)
            encoding = con.info().get_content_charset('utf8')
            data2 = json.loads(con.read().decode(encoding))

            avg_wr = data1.get("header").get('wr')

            df_top['AVG Win Rate'][rowname] = avg_wr
            df_jg['AVG Win Rate'][rowname] = avg_wr
            df_mid['AVG Win Rate'][rowname] = avg_wr
            df_bot['AVG Win Rate'][rowname] = avg_wr
            df_sup['AVG Win Rate'][rowname] = avg_wr
            tm_top['AVG Win Rate'][rowname] = avg_wr
            tm_jg['AVG Win Rate'][rowname] = avg_wr
            tm_mid['AVG Win Rate'][rowname] = avg_wr
            tm_bot['AVG Win Rate'][rowname] = avg_wr
            tm_sup['AVG Win Rate'][rowname] = avg_wr

            for i in range(50):
                win_rate = data1.get('enemy_top')[i][2] / data1.get('enemy_top')[i][1] * 100
                df_top[cid_dict.get(data1.get('enemy_top')[i][0])][rowname] = win_rate
            for i in range(50):
                win_rate = data1.get('enemy_jungle')[i][2] / data1.get('enemy_jungle')[i][1] * 100
                df_jg[cid_dict.get(data1.get('enemy_jungle')[i][0])][rowname] = win_rate
            for i in range(55):
                win_rate = data1.get('enemy_middle')[i][2] / data1.get('enemy_middle')[i][1] * 100
                df_mid[cid_dict.get(data1.get('enemy_middle')[i][0])][rowname] = win_rate
            for i in range(28):
                win_rate = data1.get('enemy_bottom')[i][2] / data1.get('enemy_bottom')[i][1] * 100
                df_bot[cid_dict.get(data1.get('enemy_bottom')[i][0])][rowname] = win_rate
            for i in range(38):
                win_rate = data1.get('enemy_support')[i][2] / data1.get('enemy_support')[i][1] * 100
                df_sup[cid_dict.get(data1.get('enemy_support')[i][0])][rowname] = win_rate

            if data2.get('team_top'):
                for i in range(50):
                    win_rate = data2.get('team_top')[i][2] / data2.get('team_top')[i][1] * 100
                    tm_top[cid_dict.get(data2.get('team_top')[i][0])][rowname] = win_rate
            if data2.get('team_jungle'):
                for i in range(50):
                    win_rate = data2.get('team_jungle')[i][2] / data2.get('team_jungle')[i][1] * 100
                    tm_jg[cid_dict.get(data2.get('team_jungle')[i][0])][rowname] = win_rate
            if data2.get('team_middle'):
                for i in range(55):
                    win_rate = data2.get('team_middle')[i][2] / data2.get('team_middle')[i][1] * 100
                    tm_mid[cid_dict.get(data2.get('team_middle')[i][0])][rowname] = win_rate
            if data2.get('team_bottom'):
                for i in range(28):
                    win_rate = data2.get('team_bottom')[i][2] / data2.get('team_bottom')[i][1] * 100
                    tm_bot[cid_dict.get(data2.get('team_bottom')[i][0])][rowname] = win_rate
            if data2.get('team_support'):
                for i in range(38):
                    win_rate = data2.get('team_support')[i][2] / data2.get('team_support')[i][1] * 100
                    tm_sup[cid_dict.get(data2.get('team_support')[i][0])][rowname] = win_rate

    # df for enemy, tm for teammate
    return df_top, df_jg, df_mid, df_bot, df_sup, tm_top, tm_jg, tm_mid, tm_bot, tm_sup
