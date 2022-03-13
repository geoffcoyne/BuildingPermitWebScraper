from __future__ import division
import csv
from logging import exception
from mailbox import NoSuchMailboxError
import multiprocessing
from selenium import webdriver
from selenium.webdriver.common import by
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from pyvirtualdisplay import Display

## HOW TO USE ##

# Introduction #
# This scrapper is designed to collect the number of bedrooms, square footage, total dwelling units, and esitmated costs for building permits in Louisville metro. 
# It was created because Louisville Metro does not provide this data in a list for every permit. It is designed to be compatible with the Louisville Metro Buisness Portal
# and it may be compatible with similar sites however it has not been tested.

# Instructions #
# This tool uses Google Chrome and Chrome Web Driver, both must be downloaded and able to be lauched from PATH on your system.
# To use this tool you will need a CSV file containing building permits for a city with the record numbers contained in a column titled "Record Number."
# You will also need to supply a copy of that CSV file with feilds for the new data. Those should be appened to the end as follows:
# "Number of Bedrooms", "Square Footage House", "Total Number of Dwelling Units", "Estimated Cost", and "Data Collection Failed?" 
# The program will out put a file containing the permits and the new data it gathered and whether data collection was successful for each permit.

## EDIT THESE VARIABLES TO FIT YOUR USE CASE ##
PermitFileName = 'example.csv' # Enter the name of the file containing permits
PermitFileWithNewFeilds = 'examplewithfields.csv' # Enter the name of the file with fields appended
OutputFileName = 'exampleoutput.csv' # Enter the desired output name
PermitDateStart = '01012001' # Enter the earliest date of the permits in your file formated as MM/DD/YYYY without the /'s (ie 01/01/2001 would be written as 01012001)
PermitDateEnd = '12122012' # Enter the latest date of the permits in your file formated as MM/DD/YYYY without the /'s (ie 01/01/2001 would be written as 01012001)
NumberOfPermits = 0 # The number of permits in your permit file (not required, only used for displaying a progress estimate)
NumberOfThreads = 1 # The number of instances of Selenium you want to run should be similar to the number of cores in your system for fastest execution
BuildingPermitSearch = 'https://aca-prod.accela.com/LJCMG/Cap/CapHome.aspx?module=Building&TabName=Building&TabList=Home%7C0%7CAPCD%7C1%7CBuilding%7C2%7CEnforcement%7C3%7CLicenses%7C4%7CPlanning%7C5%7CPublicWorks%7C6%7CCurrentTabIndex%7C2' #URL for the permit search, default is Louisville Metro's Permit Search. As stated the program is only tested with Louisville Metro's and may not function with other cities.

recordNums = []
newData = []
counter = 0 

# Pulls Record Numbers from CSV file and adds them to recordNum list
def readRecordList():
    with open(PermitFileName, newline='', encoding='utf-8 ') as csvFile:
        reader = csv.DictReader(csvFile)
        for row in reader:
            recordNums.append(row['Record Number'])
            

# Bot that gathers data and adds it to newData 2D list

def getRecordData(currentRecord):
    global counter
    currentPermitData = {'Number of Bedrooms':'', 'Square Footage House':'', 'Total Number of Dwelling Units':'', 'Estimated Cost':'', 'Data Collection Failed?':False}
    try:
        display = Display(visible=False, size=(800,600))
        display.start()
    except:
        print('Display failed to start...')
        currentPermitData['Data Collection Failed?'] = True
        counter += 1
        display.stop()
        return currentPermitData
    try:
        chromeOptions = webdriver.ChromeOptions()
        chromeOptions.add_argument('--no-sandbox')
        browser = webdriver.Chrome(options=chromeOptions)
        browser.get(BuildingPermitSearch)
    except:
        print('Browser failed to start...')
        currentPermitData['Data Collection Failed?'] = True
        counter += 1
        browser.quit()
        display.stop()
        return currentPermitData
    try:
        recordNumField = browser.find_element(By.ID, 'ctl00_PlaceHolderMain_generalSearchForm_txtGSPermitNumber')
        dateStartField = browser.find_element(By.ID, 'ctl00_PlaceHolderMain_generalSearchForm_txtGSStartDate')
        dateEndField = browser.find_element(By.ID, 'ctl00_PlaceHolderMain_generalSearchForm_txtGSEndDate')
        searchButton = browser.find_element(By.ID, 'ctl00_PlaceHolderMain_btnNewSearch')
        recordNumField.send_keys(currentRecord)
        for n in range(0,8):
            dateStartField.send_keys(Keys.BACK_SPACE)
        dateStartField.send_keys('01012004')
        for n in range(0,8):
            dateEndField.send_keys(Keys.BACK_SPACE)
        dateEndField.send_keys('12312020')
        searchButton.click()
    
        WebDriverWait(browser, 20).until(
            expected_conditions.presence_of_element_located((By.CLASS_NAME, 'MoreDetail_ItemCol1'))
        )

        # Opening Collapsable Information
        moreDet = browser.find_element(By.ID, 'lnkMoreDetail')
        moreDet.click()
        moreLnk = browser.find_element(By.ID, 'lnkASI')
        moreLnk.click() 
        # Creates list of Info available
        moreCol1 = browser.find_elements(By.CSS_SELECTOR, '.MoreDetail_ItemCol1 > span')
        moreCol2 = browser.find_elements(By.CSS_SELECTOR, '.MoreDetail_ItemCol2 > span')
        col2Counter = 0
        for n in moreCol1:
            if n.text == '':
                col2Counter -= 1
            elif n.text == 'Total No.Bedrooms:':
                currentPermitData['Number of Bedrooms'] = (moreCol2[col2Counter].text)
            elif n.text == 'Square footage:':
                currentPermitData['Square Footage House'] = (moreCol2[col2Counter].text)
            elif n.text == 'Total No. Dwell Units:':
                currentPermitData['Total Number of Dwelling Units'] = (moreCol2[col2Counter].text)
            elif n.text == 'Estimated Cost:':
                currentPermitData['Estimated Cost'] = (moreCol2[col2Counter].text)
            col2Counter += 1
            
    except:
        currentPermitData['Data Collection Failed?'] = True
        print('The current record (', currentRecord, ') could not be obtained.')
        counter += 1
        browser.quit()
        display.stop()
        return currentPermitData
    browser.quit()
    display.stop()
    counter+=1
    print (counter*NumberOfThreads, ' complete! ', round(counter/(NumberOfPermits/NumberOfThreads)*100, 2), '% of the total!')
    return currentPermitData

# Adds Data from Louisville Metro Buisness Portal website to RecordListWithDetailsAdded.csv
def createCSV(newData):
    input('Press <ENTER> to Begin Writing Data to CSV\'s (Program will close when finished)')
    print('\n')
    #print(newData)
    with open(PermitFileWithNewFeilds, 'r', newline='', encoding='utf-8') as csvWithDetails, open(OutputFileName, 'w', newline='', encoding='utf-8') as csvWithAltersWrite:
        reader = csv.DictReader(csvWithDetails)
        writer = csv.DictWriter(csvWithAltersWrite, fieldnames=reader.fieldnames)
        writer.writeheader()
        for row in reader:
            writer.writerow({'Date': row['Date'],
                            'Record Number': row['Record Number'],
                            'Project Name': row['Project Name'],
                            'Address': row['Address'],
                            'Status': row['Status'],
                            'Description': row['Description'],
                            'Expiration Date': row['Expiration Date'],
                            'Short Notes': row['Short Notes'],
                            'Number of Bedrooms': newData[n]['Number of Bedrooms'],
                            'Square Footage House': newData[n]['Square Footage House'],
                            'Total Number of Dwelling Units': newData[n]['Total Number of Dwelling Units'],
                            'Estimated Cost': newData[n]['Estimated Cost'],
                            'Data Collection Failed?': newData[n]['Data Collection Failed?']})

# Creating Pools
if __name__ == '__main__':
    readRecordList()
    with multiprocessing.Pool(processes=NumberOfThreads, initializer=None) as pool:
        newData = pool.map(getRecordData, recordNums)
                  
    createCSV(newData)

    

