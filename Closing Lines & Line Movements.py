# import socket
# import socks
import requests
from bs4 import BeautifulSoup
import datetime
from datetime import date
import time
from pandas import DataFrame
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import re
import os


# def connectTor():
#     # Connect to Tor for privacy purposes
#     socks.setdefaultproxy(socks.PROXY_TYPE_SOCKS5, '127.0.0.1', 9150, True)
#     socket.socket = socks.socksocket
#     print("connected to Tor!")


def soup_url(type_of_line, tdate=str(date.today()).replace('-', ''), driver=None):
    # get html code for odds based on desired line type and date
    line_types = {
        'ML': '',
        'RL': 'pointspread/',
        'total': 'totals/',
        '1H': '1st-half/',
        '1HRL': 'pointspread/1st-half/',
        '1Htotal': 'totals/1st-half/'
    }
    url_addon = line_types[type_of_line]
    url = 'http://classic.sportsbookreview.com/betting-odds/mlb-baseball/' + url_addon + '?date=' + tdate
    timestamp = time.strftime("%H:%M:%S")
    # needs to run through line_movement_soup to get

    driver.get(url)

    if type_of_line in ('RL', '1HRL'):
        game_half = 'Full Game' if type_of_line == 'RL' else '1st Half'
        soup_big = BeautifulSoup(driver.page_source, 'html.parser')
        soup = soup_big.find_all('div', id='OddsGridModule_3')[0]
        line_movement_soup(soup, tdate, driver, game_half)
    else:
        # ML, total, 1H, 1Htotal
        soup_big = BeautifulSoup(requests.get(url).text, 'html.parser')
        soup = soup_big.find_all('div', id='OddsGridModule_3')[0]

    return soup, timestamp


def line_movement_soup(soup, game_date, driver, game_half):
    """ only pull once for 1h and for full game, not 3 times """
    book_list = [
        ('238', 'Pinnacle'),
        ('19', '5Dimes'),
        ('999996', 'Bovada'),
        ('1096', 'BetOnline'),
        ('169', 'Heritage')]

    # Pitcher_Names to pass to line movement file
    A_pit_list = []
    H_pit_list = []
    all_pit_info = soup.find_all('div', attrs={'class': 'el-div eventLine-team'})
    for ngames in range(len(all_pit_info)):
        A_pit_info  = all_pit_info[ngames].find_all('div')[1].get_text().strip()
        H_pit_info  = all_pit_info[ngames].find_all('div')[2].get_text().strip()
        A_pit       = A_pit_info[A_pit_info.find('-') + 2 : A_pit_info.find("(") - 1]
        H_pit       = H_pit_info[H_pit_info.find('-') + 2 : H_pit_info.find("(") - 1]
        A_pit_list.append(A_pit)
        H_pit_list.append(H_pit)

    eventlines = soup.find_all('div', {'class': 'el-div eventLine-book'})
    for num in range(len(eventlines)):
        a_pit_name = A_pit_list[num // 10]
        h_pit_name = H_pit_list[num // 10]

        eventcode = eventlines[num]
        eventid = eventcode['id']
        book_id = eventid[[m.start() for m in re.finditer(r"-", eventid)][1] + 1:]
        if book_id in [tup[0] for pos, tup in enumerate(book_list)]:
            book_name = [tup[1] for pos, tup in enumerate(book_list) if tup[0] == book_id][0]

            try:
                # Open popup
                driver.find_element_by_xpath("//div[@id='" + eventid + "']").click()
    
                # Timer to let popup load
                time.sleep(1)
                wait_for_popup = True
                start_timer = time.time()
                while (wait_for_popup == True and time.time() - start_timer <= 10):
                    popup_soup = BeautifulSoup(driver.page_source, 'html.parser')
                    if len(popup_soup.find_all('div', attrs={'class': 'info-box'})) > 0:
                        wait_for_popup = False
                        break
                    else:
                        print('sleep 1 more second')
                        time.sleep(1)
    
    
                all_line_changes = get_line_move_data(popup_soup, game_date, game_half, book_name, a_pit_name,h_pit_name)
                # Print statement wont print(all eventlines because of the if statement
                print('writing ' + game_half + ' line movement -- ' + str(num+1) + ' / ' + str(len(eventlines)))
    
                with open(os.getcwd()+'\\SBR_MLB_Lines_'+season+'_line_moves.txt', 'a') as f:
                    all_line_changes.to_csv(f, index=False, header = False)
    
                # CLose popup
                driver.find_element_by_xpath("//span[@class='ui-button-icon-primary ui-icon ui-icon-closethick']").click()
            except:
                print('skipped one link')
                pass
                
def get_line_move_data(soup,game_date,game_half,book_name,a_pit_name,h_pit_name,line_change_list = []):
    def prettify_odds(r,ha):
        # input should be one or 2, depending on if i want away or home data
        # Appends lines and odds to list to write to DF
        if t != 1: # to split up odds and line
            d = row_data[ha].get_text().replace(u'\xa0', ' ').replace(u'\xbd', '.5')
            line = d[:d.index(' ')]
            odds = d[d.index(' ')+1:]
            line_change_list.extend([line, odds])
        else: # to only grab moneyline
            line = ''
            odds = row_data[ha].get_text()
            odds_trimmed = odds[odds.find('+') if odds.find('+') > 0 else odds.find('-'):]
            line_change_list.extend([line, odds_trimmed])

    df_line_moves = DataFrame(columns=('Date', 'Team', 'Team SP', 'Opponent', 'Opponent SP', 'Full or Half Game?', 'Line Type', 'Time of Line Change', 'over.under', 'Line', 'Odds'))
    stats_tables = soup.find_all('div', attrs={'class': 'info-box'})
    num_tables = len(stats_tables)

    away_team = team_name_check(stats_tables[0].find_all('table')[0].find_all('tr')[0].find_all('td')[1].get_text())
    home_team = team_name_check(stats_tables[0].find_all('table')[0].find_all('tr')[0].find_all('td')[2].get_text())

    for t in range(num_tables):
        stats_table_name = stats_tables[t].find_all('div')[0].get_text()
        row = stats_tables[t].find_all('table')[1].find_all('tr')
        for r in reversed(range(len(row))):
            row_data = row[r].find_all('td')
            time_of_move = row_data[0].get_text()
            for dub in range(1, 3):
                line_change_list = []
                line_change_list.extend([game_date])
                if dub == 1:
                    o_u_checker = 'over' if t == 2 else ''
                    line_change_list.extend([away_team, a_pit_name, home_team, h_pit_name])
                else:
                    o_u_checker = 'under' if t == 2 else ''
                    line_change_list.extend([home_team, h_pit_name, away_team, a_pit_name])
                line_change_list.extend([game_half, stats_table_name, time_of_move, o_u_checker])
                prettify_odds(row_data, dub)
                df_line_moves.loc[len(df_line_moves) + 1] = ([line_change_list[j].replace(u'\xa0', ' ').replace(u'\xbd', '.5') for j in range(len(line_change_list))])
    return df_line_moves


def parse_and_write_data(soup, date, time_of_move, not_ML=True):
    """
    Parse HTML to gather line data by book
    ML lines are simpler to parse, so we need an option to know which type of
    parsing needs to be done.

    using ['238', '19', '999996', '1096', '169']
    BookID  BookName
    238     Pinnacle
    19      5Dimes
    999996  Bovada
    1096    BetOnline
    169     Heritage
    93      Bookmaker
    123     BetDSI
    139     Youwager
    999991  SIA
    """
    def book_line(book_id, line_id, homeaway):
        """
        Get Line info given a book ID.
        Since each book has their own html value, this is how we can parse each book separately
        """           
        try:
            lo0 = soup.find_all('div', attrs={'class': 'el-div eventLine-book', 'rel': book_id})
            lo0 = lo0[line_id]
            lo0 = lo0.find_all('div')
            lo0 = lo0[homeaway]
            lo0 = lo0.get_text().strip()
            lo1 = lo0.replace(u'\xa0', ' ').replace(u'\xbd', '.5')
            line_split = lo1.find(' ')
            line = lo1[:line_split]
            odds = lo1[line_split + 1:]
        except IndexError:
            line = ''
            odds = ''
        return line, odds

    if not_ML:
        df = DataFrame(
            columns=('key', 'date', 'time', 'H/A',
                     'team', 'pitcher', 'hand',
                     'opp_team', 'opp_pitcher',
                     'opp_hand',
                     'pinnacle_line', 'pinnacle_odds',
                     '5dimes_line', '5dimes_odds',
                     'heritage_line', 'heritage_odds',
                     'bovada_line', 'bovada_odds',
                     'betonline_line', 'betonline_odds'))
    else:
        df = DataFrame(
            columns=('key', 'date', 'time', 'H/A',
                     'team', 'pitcher', 'hand',
                     'opp_team', 'opp_pitcher',
                     'opp_hand', 'pinnacle', '5dimes',
                     'heritage', 'bovada', 'betonline'))

    counter = 0
    number_of_games = len(soup.find_all('div', attrs={'class': 'el-div eventLine-rotation'}))
    # print('number of games:' + str(number_of_games))
    for i in range(0, number_of_games):
        A = []
        H = []
        print(str(i + 1) +'/' + str(number_of_games))

        info_A =                soup.find_all('div', attrs={'class': 'el-div eventLine-team'})[i].find_all('div')[0].get_text().strip()
        hyphen_A =              info_A.find('-')
        paren_A =               info_A.find("(")
        team_A =                info_A[:hyphen_A - 1]
        pitcher_A =             info_A[hyphen_A + 2 : paren_A - 1]
        hand_A =                info_A[paren_A + 1 : -1]

        info_H =                soup.find_all('div', attrs={'class': 'el-div eventLine-team'})[i].find_all('div')[2].get_text().strip()
        hyphen_H =              info_H.find('-')
        paren_H =               info_H.find("(")
        team_H =                info_H[:hyphen_H - 1]
        pitcher_H =             info_H[hyphen_H + 2 : paren_H - 1]
        hand_H =                info_H[paren_H + 1 : -1]

        pinnacle_A_lines, pinnacle_A_odds   = book_line('238', i, 0)
        fivedimes_A_lines, fivedimes_A_odds = book_line('19', i, 0)
        heritage_A_lines, heritage_A_odds   = book_line('169', i, 0)
        bovada_A_lines, bovada_A_odds       = book_line('999996', i, 0)
        betonline_A_lines, betonline_A_odds = book_line('1096', i, 0)

        pinnacle_H_lines, pinnacle_H_odds   = book_line('238', i, 1)
        fivedimes_H_lines, fivedimes_H_odds = book_line('19', i, 1)
        heritage_H_lines, heritage_H_odds   = book_line('169', i, 1)
        bovada_H_lines, bovada_H_odds       = book_line('999996', i, 1)
        betonline_H_lines, betonline_H_odds = book_line('1096', i, 1)

        # Edit team names to match personal preference
        team_H = team_name_check(team_H)
        team_A = team_name_check(team_A)

        A.append(str(date) + '_' + team_A.replace(u'\xa0', ' ') + '_' + team_H.replace(u'\xa0', ' '))
        A.extend([date, time_of_move, 'away', team_A, pitcher_A, hand_A, team_H, pitcher_H, hand_H])

        # Account for runline and totals. Usually come in format '7 -110' or '-0.5 -110'.
        # Use these if statements to separate line from odds
        if not_ML:
            # write pinnacle data in list
            A.extend([pinnacle_A_lines, pinnacle_A_odds,
                      fivedimes_A_lines, fivedimes_A_odds,
                      heritage_A_lines, heritage_A_odds,
                      bovada_A_lines, bovada_A_odds,
                      betonline_A_lines, betonline_A_odds])
        else:
            # write ML book data in list
            A.extend([pinnacle_A_odds,
                      fivedimes_A_odds,
                      heritage_A_odds,
                      bovada_A_odds,
                      betonline_A_odds])

        H.append(str(date) + '_' + team_A.replace(u'\xa0', ' ') + '_' + team_H.replace(u'\xa0', ' '))
        H.extend([date, time_of_move, 'home', team_H, pitcher_H, hand_H, team_A, pitcher_A, hand_A])
        if not_ML:
            # write pinnacle data in list
            H.extend([pinnacle_H_lines, pinnacle_H_odds,
                      fivedimes_H_lines, fivedimes_H_odds,
                      heritage_H_lines, heritage_H_odds,
                      bovada_H_lines, bovada_H_odds,
                      betonline_H_lines, betonline_H_odds])
        else:
            # write ML book data in list
            H.extend([pinnacle_H_odds,
                      fivedimes_H_odds,
                      heritage_H_odds,
                      bovada_H_odds,
                      betonline_H_odds])

        # Write List (A & H) into dataframe
        df.loc[counter]     = ([A[j] for j in range(len(A))])
        df.loc[counter + 1] = ([H[j] for j in range(len(H))])
        counter += 2
    return df


def select_and_rename(df, text):
    # Select only useful column names
    # Rename column names so that when merged, each df will be unique
    if text[-2:] == 'ml':
        df = df[['key', 'time', 'team', 'pitcher', 'hand', 'opp_team',
                 'pinnacle', '5dimes', 'heritage', 'bovada', 'betonline']]
    # Change column names to make them unique
        df.columns = ['key', text + '_time', 'team', 'pitcher', 'hand', 'opp_team',
                      text + '_PIN', text + '_FD', text + '_HER', text + '_BVD', text + '_BOL']
    else:
        df = df[['key', 'time', 'team', 'pitcher', 'hand', 'opp_team',
                 'pinnacle_line', 'pinnacle_odds',
                 '5dimes_line', '5dimes_odds',
                 'heritage_line', 'heritage_odds',
                 'bovada_line', 'bovada_odds',
                 'betonline_line', 'betonline_odds']]
        df.columns = ['key', text + '_time', 'team', 'pitcher', 'hand', 'opp_team',
                      text + '_PIN_line', text + '_PIN_odds',
                      text + '_FD_line', text + '_FD_odds',
                      text + '_HER_line', text + '_HER_odds',
                      text + '_BVD_line', text + '_BVD_odds',
                      text + '_BOL_line', text + '_BOL_odds']
    return df


def team_name_check(team_name):
    """lookup teams wtih weird acronyms"""
    lookup = {
        'LA': 'LAD',
        'SD': 'SDG',
        'SF': 'SFO',
        'NY': 'NYM',
        'KC': 'KCA',
        'TB': 'TBA',
        'CWS': 'CHW',
        'CHI': 'CHC',
        'WSH': 'WAS'
    }

    try:
        new_team_name = lookup[team_name]
    except:
        new_team_name = team_name

    return new_team_name


def main(profile, season, inputdate=str(date.today()).replace('-', '')):
    """
    Get lines for a given day.

    1) soup_*: store all soup data for each bet type in their own variable
        a) RL and 1HRL get loaded via their own special process
        b) the rest are just called via requests
    2) parse_and_write_data: 
    """
    driver = webdriver.Firefox(firefox_profile=profile)


    # store BeautifulSoup info for parsing
    print("getting today's MoneyLine (1/6)")
    soup_ml, time_ml = soup_url('ML', inputdate, driver)

    print("getting today's RunLine (2/6)")
    soup_rl, time_rl = soup_url('RL', inputdate, driver)

    print("getting today's totals (3/6)")
    soup_tot, time_tot = soup_url('total', inputdate, driver)

    print("getting today's 1st-half MoneyLine (4/6)")
    soup_1h_ml, time_1h_ml = soup_url('1H', inputdate, driver)

    print("getting today's 1st-half RunLine (5/6)")
    soup_1h_rl, time_1h_rl = soup_url('1HRL', inputdate, driver)

    print("getting today's 1st-half totals (6/6)")
    soup_1h_tot, time_1h_tot = soup_url('1Htotal', inputdate, driver)

    # Parse and Write
    print("writing today's MoneyLine (1/6)")
    df_ml = parse_and_write_data(soup_ml, inputdate, time_ml, not_ML=False)
    # Change column names to make them unique
    df_ml.columns = ['key', 'date', 'ml_time', 'H/A', 'team', 'pitcher',
                     'hand', 'opp_team', 'opp_pitcher', 'opp_hand',
                     'ml_PIN', 'ml_FD', 'ml_HER', 'ml_BVD', 'ml_BOL']

    print("writing today's RunLine (2/6)")
    df_rl = parse_and_write_data(soup_rl, inputdate, time_rl)
    df_rl = select_and_rename(df_rl, 'rl')

    print("writing today's totals (3/6)")
    df_tot = parse_and_write_data(soup_tot, inputdate, time_tot)
    df_tot = select_and_rename(df_tot, 'tot')

    print("writing today's 1st-half MoneyLine (4/6)")
    df_1h_ml = parse_and_write_data(soup_1h_ml, inputdate, time_1h_ml, not_ML =False)
    df_1h_ml = select_and_rename(df_1h_ml, '1h_ml')

    print("writing today's 1st-half RunLine (5/6)")
    df_1h_rl = parse_and_write_data(soup_1h_rl, inputdate, time_1h_rl)
    df_1h_rl = select_and_rename(df_1h_rl, '1h_rl')

    print("writing today's 1st-half totals (6/6)")
    df_1h_tot = parse_and_write_data(soup_1h_tot, inputdate, time_1h_tot)
    df_1h_tot = select_and_rename(df_1h_tot, '1h_tot')

    # Write to Dataframes
    write_df = df_ml
    write_df = write_df.merge(
        df_rl, how='left', on=['key', 'team', 'pitcher', 'hand', 'opp_team'])
    write_df = write_df.merge(
        df_tot, how='left', on=['key', 'team', 'pitcher', 'hand', 'opp_team'])
    write_df = write_df.merge(
        df_1h_ml, how='left', on=['key', 'team', 'pitcher', 'hand', 'opp_team'])
    write_df = write_df.merge(
        df_1h_rl, how='left', on=['key', 'team', 'pitcher', 'hand', 'opp_team'])
    write_df = write_df.merge(
        df_1h_tot, how='left', on=['key', 'team', 'pitcher', 'hand', 'opp_team'])

    # Write to txt
    with open(os.getcwd() + '\\SBR_MLB_Closing_Lines_' + season + '.txt', 'a') as f:
        write_df.to_csv(f, index=False, header=False)

    driver.close()

def write_date(filename, dt, sport='MLB'):
    filename = os.getcwd() + '/SBR_{}_Lines_{}_games.txt'.format(sport, filename)
    f = open(filename, 'a+')
    f.write(dt + '\n')
    f.close()


def check_date(dt, sport='MLB'):
    filename = os.getcwd() + '/SBR_{}_Lines_{}_games.txt'.format(sport, 'good')
    f = open(filename, 'r+')

    good = f.readlines()
    f.close()

    if dt in good:
        return True

    return False


def run_main(driver, season, month=1):
    """
    This function loops over every date from the beginning of the entered month.

    It also stores a list of completed or failed dates for future iterations as this
    is a slow program that could take multiple hours to run. This provides a way to avoid
    rerunning the same day.
    """
    month = int(month)
    days_in_month_lookup = {
        1: 31,
        2: 28,
        3: 31,
        4: 30,
        5: 31,
        6: 30,
        7: 31,
        8: 31,
        9: 30,
        10: 31,
        11: 30,
        12: 31
    }
    days_in_month = days_in_month_lookup[month]
    # Convert month to two characters
    month = str(month + 1).rjust(2, '0')
    for z in range(days_in_month):
        z = str(z + 1).rjust(2, '0')
        lookupdate = season + month + z
        lookupdate_to_write = '{}/{}/{}'.format(season, month, z)
        print(lookupdate_to_write)

        if not check_date(dt=lookupdate_to_write):
            try:
                main(driver, season, lookupdate)
                write_date(filename='good', dt=lookupdate_to_write)
            except KeyboardInterrupt:
                break
            except:
                write_date(filename='bad', dt=lookupdate_to_write)
                print()
                print('bad game -- ' + lookupdate)
                print()
                pass


if __name__ == '__main__':
    # connectTor()
    season = str(input("Please type the year for which you would like to pull data (yyyy):"))
    start_month = input("Please type the starting month for which you would like to pull data (1-12):")
    end_month = input("Please type the last month for which you would like to pull data (1-12):")

    # Add Column Headers
    f = open(os.getcwd() + '\\SBR_MLB_Closing_Lines_' + season + '.txt', 'a')
    f.write('Game_ID,Date,Time_FG_ML,HA,Team,Team_SP,Team_SP_hand,Opp,Opp_SP,Opp_SP_hand,')
    f.write('FG_ML_PIN,FG_ML_FD,FG_ML_HER,FG_ML_BVD,FG_ML_BOL,')
    f.write('Time_FG_RL,FG_RL_Line_PIN,FG_RL_Odds_PIN,FG_RL_Line_FD,FG_RL_Odds_FD,FG_RL_Line_HER,FG_RL_Odds_HER,FG_RL_Line_BVD,FG_RL_Odds_BVD,FG_RL_Line_BOL,FG_RL_Odds_BOL,')
    f.write('Time_FG_Tot,FG_Tot_Line_PIN,FG_Tot_Odds_PIN,FG_Tot_Line_FD,FG_Tot_Odds_FD,FG_Tot_Line_HER,FG_Tot_Odds_HER,FG_Tot_Line_BVD,FG_Tot_Odds_BVD,FG_Tot_Line_BOL,FG_Tot_Odds_BOL,')
    f.write('Time_FF_ML,FF_ML_PIN,FF_ML_FD,FF_ML_HER,FF_ML_BVD,FF_ML_BOL,')
    f.write('Time_FF_RL,FF_RL_Line_PIN,FF_RL_Odds_PIN,FF_RL_Line_FD,FF_RL_Odds_FD,FF_RL_Line_HER,FF_RL_Odds_HER,FF_RL_Line_BVD,FF_RL_Odds_BVD,FF_RL_Line_BOL,FF_RL_Odds_BOL,')
    f.write('Time_FF_RL,FF_Tot_Line_PIN,FF_Tot_Odds_PIN,FF_Tot_Line_FD,FF_Tot_Odds_FD,FF_Tot_Line_HER,FF_Tot_Odds_HER,FF_Tot_Line_BVD,FF_Tot_Odds_BVD,FF_Tot_Line_BOL,FF_Tot_Odds_BOL')
    f.write('\n')
    f.close()

    f = open(os.getcwd() + '\\SBR_MLB_Lines_' + season + '_line_moves.txt', 'a')
    f.write('Date,Team,Team_SP,Opp,Opp_SP,Bet_Length,Bet_Type,Line_Move_Time,Over_Under,Line,Odds')
    f.write('\n')
    f.close()

    ##
    from selenium import webdriver
    from selenium.webdriver.firefox.firefox_profile import FirefoxProfile
    import os

    # torexe = os.popen(r'/home/kc/Downloads/tor-browser_en-US/Browser/TorBrowser/Tor/tor.exe')
    profile = FirefoxProfile(r'/home/kc/Downloads/tor-browser_en-US/Browser/TorBrowser/Data/Browser/profile.default')
    profile.set_preference('network.proxy.type', 1)
    profile.set_preference('network.proxy.socks', '127.0.0.1')
    profile.set_preference('network.proxy.socks_port', 9150)
    profile.set_preference("network.proxy.socks_remote_dns", False)
    profile.update_preferences()
    # driver.get("http://check.torproject.org")

    #
    time.sleep(5)
    # driver = webdriver.Firefox(profile)

    # driver = webdriver.Chrome("C:/users/kj/desktop/chromedriver.exe")
    # time.sleep(3)
    # to uitilize a headless driver, download and install phantomjs and use below to open driver instead of above line
    # download link -- http://phantomjs.org/download.html
    # driver = webdriver.PhantomJS(r"C:\Users\Monstar\Python\phantomjs-2.0.0\bin\phantomjs.exe")

    for y in range(int(start_month) - 1, int(end_month)):
        try:
            run_main(profile, season, y)
        except KeyboardInterrupt:
            break