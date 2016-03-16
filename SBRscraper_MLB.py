import socket
import socks
import requests
from bs4 import BeautifulSoup
import datetime
from datetime import date
import time
from pandas import DataFrame

def connectTor():
## Connect to Tor for privacy purposes
    socks.setdefaultproxy(socks.PROXY_TYPE_SOCKS5, '127.0.0.1', 9150, True)
    socket.socket = socks.socksocket
    print "connected to Tor!"

def soup_url(type_of_line, tdate = str(date.today()).replace('-','')):
## get html code for odds based on desired line type and date

    web_url = dict()
    web_url['ML'] = ''
    web_url['RL'] = 'pointspread/'
    web_url['total'] = 'totals/'
    web_url['1H'] = '1st-half/'
    web_url['1HRL'] = 'pointspread/1st-half'
    web_url['1Htotal'] = 'totals/1st-half'
    url_addon = web_url[type_of_line]

    url = 'http://www.sbrforum.com/betting-odds/mlb-baseball/' + url_addon + '?date=' + tdate
    now = datetime.datetime.now()
    raw_data = requests.get(url)
    soup_big = BeautifulSoup(raw_data.text, 'html.parser')
    soup = soup_big.find_all('div', id='OddsGridModule_3')[0]
    timestamp = time.strftime("%H:%M:%S")
    return soup, timestamp

def replace_unicode(string):
    return string.replace(u'\xa0',' ').replace(u'\xbd','.5')

def parse_and_write_data(soup, date, time, not_ML = True):
## Parse HTML to gather line data by book
    def book_line(book_id, line_id, homeaway):
        ## Get Line info from book ID
        line = soup.find_all('div', attrs = {'class':'el-div eventLine-book', 'rel':book_id})[line_id].find_all('div')[homeaway].get_text().strip()
        return line
    '''
    BookID  BookName
    238     Pinnacle
    19      5Dimes
    93      Bookmaker
    1096    BetOnline
    169     Heritage
    123     BetDSI
    999996  Bovada
    139     Youwager
    999991  SIA
    '''
    if not_ML:
        df = DataFrame(
                columns=('key','date','time','H/A',
                         'team','pitcher','hand',
                         'opp_team','opp_pitcher',
                         'opp_hand',
                         'pinnacle_line','pinnacle_odds',
                         '5dimes_line','5dimes_odds',
                         'heritage_line','heritage_odds',
                         'bovada_line','bovada_odds',
                         'betonline_line','betonline_odds'))
    else:
        df = DataFrame(
            columns=('key','date','time','H/A',
                     'team','pitcher','hand',
                     'opp_team','opp_pitcher',
                     'opp_hand','pinnacle','5dimes',
                     'heritage','bovada','betonline'))
    counter = 0
    number_of_games = len(soup.find_all('div', attrs = {'class':'el-div eventLine-rotation'}))
    for i in range(0, number_of_games):
        A = []
        H = []
        print str(i+1)+'/'+str(number_of_games)
        
        ## Gather all useful data from unique books
        # consensus_data = 	soup.find_all('div', 'el-div eventLine-consensus')[i].get_text()
        info_A = 		        soup.find_all('div', attrs = {'class':'el-div eventLine-team'})[i].find_all('div')[0].get_text().strip()
        hyphen_A =              info_A.find('-')
        paren_A =               info_A.find("(")
        team_A =                info_A[:hyphen_A - 1]
        pitcher_A =             info_A[hyphen_A + 2 : paren_A - 1]
        hand_A =                info_A[paren_A + 1 : -1]
        
        ## get line/odds info for unique book. Need error handling to account for blank data
        def try_except_book_line(id, i , x):
            try:
                return book_line(id, i, x)
            except IndexError:
                return ''
        
        pinnacle_A = try_except_book_line('238',i, 0)
        fivedimes_A = try_except_book_line('19',i, 0)
        heritage_A = try_except_book_line('169, i, 0)
        bovada_A = try_except_book_line('999996, i, 0)
        betonline_A = try_except_book_line('1096, i, 0)

        info_H = 		        soup.find_all('div', attrs = {'class':'el-div eventLine-team'})[i].find_all('div')[2].get_text().strip()
        hyphen_H =              info_H.find('-')
        paren_H =               info_H.find("(")
        team_H =                info_H[:hyphen_H - 1]
        pitcher_H =             info_H[hyphen_H + 2 : paren_H - 1]
        hand_H =                info_H[paren_H + 1 : -1]

        pinnacle_H = try_except_book_line('238',i, 1)
        fivedimes_H = try_except_book_line('19',i, 1)
        heritage_H = try_except_book_line('169, i, 1)
        bovada_H = try_except_book_line('999996, i, 1)
        betonline_H = try_except_book_line('1096, i, 1)

        short_to_long_abbr = dict()
        short_to_long_abbr['LA'] = 'LAD'
        short_to_long_abbr['SD'] = 'SDG'
        short_to_long_abbr['SF'] = 'SFO'
        short_to_long_abbr['NY'] = 'NYM'
        short_to_long_abbr['KC'] = 'KCA'
        short_to_long_abbr['TB'] = 'TBA'
        short_to_long_abbr['CWS'] = 'CHW'
        short_to_long_abbr['CHI'] = 'CHC'
        short_to_long_abbr['WSH'] = 'WAS'
        
        if team_H in short_to_long_abbr:
            team_H = short_to_long_abbr[team_H]
        if team_A in short_to_long_abbr:
            team_A = short_to_long_abbr[team_A]
        
        A.append(str(date) + '_' + team_A.replace(u'\xa0',' ') + '_' + team_H.replace(u'\xa0',' '))
        A.append(date)
        A.append(time)
        A.append('away')
        A.append(team_A)
        A.append(pitcher_A)
        A.append(hand_A)
        A.append(team_H)
        A.append(pitcher_H)
        A.append(hand_H)
        if not_ML:
            pinnacle_A = replace_unicode(pinnacle_A)
            pinnacle_A_line = pinnacle_A[:pinnacle_A.find(' ')]
            pinnacle_A_odds = pinnacle_A[pinnacle_A.find(' ') + 1:]
            A.append(pinnacle_A_line)
            A.append(pinnacle_A_odds)
            fivedimes_A = replace_unicode(fivedimes_A)
            fivedimes_A_line = fivedimes_A[:fivedimes_A.find(' ')]
            fivedimes_A_odds = fivedimes_A[fivedimes_A.find(' ') + 1:]
            A.append(fivedimes_A_line)
            A.append(fivedimes_A_odds)
            heritage_A = replace_unicode(heritage_A)
            heritage_A_line = heritage_A[:heritage_A.find(' ')]
            heritage_A_odds = heritage_A[heritage_A.find(' ') + 1:]
            A.append(heritage_A_line)
            A.append(heritage_A_odds)
            bovada_A = replace_unicode(bovada_A)
            bovada_A_line = bovada_A[:bovada_A.find(' ')]
            bovada_A_odds = bovada_A[bovada_A.find(' ') + 1:]
            A.append(bovada_A_line)
            A.append(bovada_A_odds)
            betonline_A = replace_unicode(betonline_A)
            betonline_A_line = betonline_A[:betonline_A.find(' ')]
            betonline_A_odds = betonline_A[betonline_A.find(' ') + 1:]
            A.append(betonline_A_line)
            A.append(betonline_A_odds)
        else:
            A.append(replace_unicode(pinnacle_A))
            A.append(replace_unicode(fivedimes_A))
            A.append(replace_unicode(heritage_A))
            A.append(replace_unicode(bovada_A))
            A.append(replace_unicode(betonline_A))
        H.append(str(date) + '_' + team_A.replace(u'\xa0',' ') + '_' + team_H.replace(u'\xa0',' '))
        H.append(date)
        H.append(time)
        H.append('home')
        H.append(team_H)
        H.append(pitcher_H)
        H.append(hand_H)
        H.append(team_A)
        H.append(pitcher_A)
        H.append(hand_A)
        if not_ML:
            pinnacle_H = replace_unicode(pinnacle_H)
            pinnacle_H_line = pinnacle_H[:pinnacle_H.find(' ')]
            pinnacle_H_odds = pinnacle_H[pinnacle_H.find(' ') + 1:]
            H.append(pinnacle_H_line)
            H.append(pinnacle_H_odds)
            fivedimes_H = replace_unicode(fivedimes_H)
            fivedimes_H_line = fivedimes_H[:fivedimes_H.find(' ')]
            fivedimes_H_odds = fivedimes_H[fivedimes_H.find(' ') + 1:]
            H.append(fivedimes_H_line)
            H.append(fivedimes_H_odds)
            heritage_H = replace_unicode(heritage_H)
            heritage_H_line = heritage_H[:heritage_H.find(' ')]
            heritage_H_odds = heritage_H[heritage_H.find(' ') + 1:]
            H.append(heritage_H_line)
            H.append(heritage_H_odds)
            bovada_H = replace_unicode(bovada_H)
            bovada_H_line = bovada_H[:bovada_H.find(' ')]
            bovada_H_odds = bovada_H[bovada_H.find(' ') + 1:]
            H.append(bovada_H_line)
            H.append(bovada_H_odds)
            betonline_H = replace_unicode(betonline_H)
            betonline_H_line = betonline_H[:betonline_H.find(' ')]
            betonline_H_odds = betonline_H[betonline_H.find(' ') + 1:]
            H.append(betonline_H_line)
            H.append(betonline_H_odds)
        else:
            H.append(replace_unicode(pinnacle_H))
            H.append(replace_unicode(fivedimes_H))
            H.append(replace_unicode(heritage_H))
            H.append(replace_unicode(bovada_H))
            H.append(replace_unicode(betonline_H))
        
        ## Take data from A and H (lists) and put them into DataFrame
        df.loc[counter]   = ([A[j] for j in range(len(A))])
        df.loc[counter+1] = ([H[j] for j in range(len(H))])
        counter += 2
    return df

def select_and_rename(df, text):
    ## Select only useful column names from a DataFrame
    ## Rename column names so that when merged, each df will be unique 
    if text[-2:] == 'ml':
        df = df[['key','time','team','pitcher','hand','opp_team',
                 'pinnacle','5dimes','heritage','bovada','betonline']]
    ## Change column names to make them unique
        df.columns = ['key',text+'_time','team','pitcher','hand','opp_team',
                      text+'_PIN',text+'_FD',text+'_HER',text+'_BVD',text+'_BOL']
    else:
        df = df[['key','time','team','pitcher','hand','opp_team',
                 'pinnacle_line','pinnacle_odds',
                 '5dimes_line','5dimes_odds',
                 'heritage_line','heritage_odds',
                 'bovada_line','bovada_odds',
                 'betonline_line','betonline_odds']]
        df.columns = ['key',text+'_time','team','pitcher','hand','opp_team',
                      text+'_PIN_line',text+'_PIN_odds',
                      text+'_FD_line',text+'_FD_odds',
                      text+'_HER_line',text+'_HER_odds',
                      text+'_BVD_line',text+'_BVD_odds',
                      text+'_BOL_line',text+'_BOL_odds']
    return df
    

def main():
    connectTor()

    ## Get today's lines
    todays_date = str(date.today()).replace('-','')
    ## change todays_date to be whatever date you want to pull in the format 'yyyymmdd'
    ## One could force user input and if results in blank, revert to today's date. 
    # todays_date = '20140611'

    ## store BeautifulSoup info for parsing
    soup_ml, time_ml = soup_url('ML', todays_date)
    print "getting today's MoneyLine (1/6)"
    soup_rl, time_rl = soup_url('RL', todays_date)
    print "getting today's RunLine (2/6)"
    soup_tot, time_tot = soup_url('total', todays_date)
    print "getting today's totals (3/6)"
    soup_1h_ml, time_1h_ml = soup_url('1H', todays_date)
    print "getting today's 1st-half MoneyLine (4/6)"
    soup_1h_rl, time_1h_rl = soup_url('1HRL', todays_date)
    print "getting today's 1st-half RunLine (5/6)"
    soup_1h_tot, time_1h_tot = soup_url('1Htotal', todays_date)
    print "getting today's 1st-half totals (6/6)"

    
    #### Each df_xx creates a data frame for a bet type
    print "writing today's MoneyLine (1/6)"
    df_ml = parse_and_write_data(soup_ml, todays_date, time_ml, not_ML = False)
    ## Change column names to make them unique
    df_ml.columns = ['key','date','ml_time','H/A','team','pitcher',
                     'hand','opp_team','opp_pitcher','opp_hand',
                     'ml_PIN','ml_FD','ml_HER','ml_BVD','ml_BOL']    

    print "writing today's RunLine (2/6)"
    df_rl = parse_and_write_data(soup_rl, todays_date, time_rl)
    df_rl = select_and_rename(df_rl, 'rl')
    
    print "writing today's totals (3/6)"
    df_tot = parse_and_write_data(soup_tot, todays_date, time_tot)
    df_tot = select_and_rename(df_tot, 'tot')
    
    print "writing today's 1st-half MoneyLine (4/6)"
    df_1h_ml = parse_and_write_data(soup_1h_ml, todays_date, time_1h_ml, not_ML = False)
    df_1h_ml = select_and_rename(df_1h_ml,'1h_ml')
    
    print "writing today's 1st-half RunLine (5/6)"
    df_1h_rl = parse_and_write_data(soup_1h_rl, todays_date, time_1h_rl)
    df_1h_rl = select_and_rename(df_1h_rl,'1h_rl')
    
    print "writing today's 1st-half totals (6/6)"
    df_1h_tot = parse_and_write_data(soup_1h_tot, todays_date, time_1h_tot)
    df_1h_tot = select_and_rename(df_1h_tot,'1h_tot')
    
    ## Merge all DataFrames together to allow for simple printout
    write_df = df_ml
    write_df = write_df.merge(
                df_rl, how='left', on = ['key','team','pitcher','hand','opp_team'])
    write_df = write_df.merge(
                df_tot, how='left', on = ['key','team','pitcher','hand','opp_team'])
    write_df = write_df.merge(
                df_1h_ml, how='left', on = ['key','team','pitcher','hand','opp_team'])
    write_df = write_df.merge(
                df_1h_rl, how='left', on = ['key','team','pitcher','hand','opp_team'])
    write_df = write_df.merge(
                df_1h_tot, how='left', on = ['key','team','pitcher','hand','opp_team'])
    
    with open('\SBR_MLB_Lines.csv', 'a') as f:
        write_df.to_csv(f, index=False)#, header = False)
  
    ## Code to pull tomorrow's data --- work in progress
    # if time.ml[:2] >= 12:
        # tomorrows_date = str(datetime.date.today() + datetime.timedelta(days=1)).replace('-','')
        # ## store BeautifulSoup info for parsing
        # soup_ml, time_ml = soup_url('ML')
        # print "getting tomorrow's MoneyLine"
        # soup_rl, time_rl = soup_url('RL')
        # print "getting tomorrow's RunLine"
        # soup_tot, time_tot = soup_url('total')
        # print "getting tomorrow's totals"
        # soup_1h_ml, time_1h_ml = soup_url('1H')
        # print "getting tomorrow's 1st-half MoneyLine"
        # soup_1h_rl, time_1h_rl = soup_url('1HRL')
        # print "getting tomorrow's 1st-half RunLine"
        # soup_1h_tot, time_1h_tot = soup_url('1Htotal')
        # print "getting tomorrow's 1st-half totals"

        # parse_and_write_data(soup_ml, todays_date, time_ml, f)
        # parse_and_write_data(soup_rl, todays_date, time_rl, f)
        # parse_and_write_data(soup_tot, todays_date, time_tot, f)
        # parse_and_write_data(soup_1h_ml, todays_date, time_1h_ml, f)
        # parse_and_write_data(soup_1h_rl, todays_date, time_1h_rl, f)
        # parse_and_write_data(soup_1h_tot, todays_date, time_1h_tot, f)

if __name__ == '__main__':
    main()
