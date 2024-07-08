import math, networkx as nx, osmnx as ox, pandas as pd, re, time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
import tkinter as tk

campus = {'A':'光復', 'B':'成功', 'C':'成杏', 'D':'自強', 'E':'力行', 'F':'敬業', 'G':'勝利'}
coor = pd.read_csv('coor.csv')
campus_list, parking_list = [], []
for i in coor['index']:
  if str(i).endswith('A'):
    parking_list.extend(coor.loc[coor['index'].values == i,'fullname'].tolist())
    parking_list = list(set(parking_list))
    campus_list.append(campus[str(i)[0]] + '校區')

## hisorty_space = pd.read_csv('history_space.csv')
## Need the file

## A == origin, B == destination ##
def GetDistance(lat_A, lon_A, lat_B, lon_B):
    G = ox.graph_from_point((22.998535, 120.218282), dist=700, network_type='walk')         ##建立node、edge圖
    ox.plot_graph(G)
    origin = ox.get_nearest_node(G, (lat_A, lon_A))                                ##起點設置
    destination = ox.get_nearest_node(G, (lat_B, lon_B))                           ##終點設置
    route = nx.shortest_path(G, origin, destination)
    return route

def setup_browser():
    url = "https://apss.oga.ncku.edu.tw/park/"
    user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/12.0.3 Safari/605.1.15"
    opt = webdriver.ChromeOptions()
    opt.add_argument('--user-agent=%s' % user_agent)
    chromedriver_path = r"C:\Users\USER\OneDrive - 國立成功大學 National Cheng Kung University\2(二)\Python程式設計與資料庫實務\final_project\chromedriver.exe"
    service = Service(chromedriver_path)
    driver = webdriver.Chrome(service=service, options=opt)
    driver.get(url)
    return driver

def find_numbers_between_tags(html, pattern=r'"number">(\d+)</span>'):
    numbers = re.findall(pattern, html)
    return [int(num) for num in numbers]

def save_to_excel(df, filename="parking_data.xlsx"):
    with pd.ExcelWriter(filename, mode='a', engine='openpyxl', if_sheet_exists='overlay') as writer:
        if 'Parking Data' in writer.book.sheetnames:
            start_row = writer.book['Parking Data'].max_row
        else:
            start_row = 0
        df.to_excel(writer, sheet_name='Parking Data', index=False, startrow=start_row)

def get_lat_lon(place_fullname, mode = 'All'):
    Lat = coor.loc[coor['fullname'] == place_fullname,'lat'].values[0]
    Lon = coor.loc[coor['fullname'] == place_fullname,'lon'].values[0]
    return Lat if mode == 'Lat' else Lon if mode == 'Lon' else (Lat, Lon)

def main(campus_target, target_place):


    ### for GUI ###
    ## Choose campus and building
    ## print section for list the choices for user
    ## input section need to swithch to what user click
    for i in campus.values():
        print(i)

    for i in campus:
      if campus[i] == campus_target:
        buildings_index = [j for j in coor['index'] if str(j).startswith(i)]
        for j in sorted(list(set(buildings_index))):
          print(coor.loc[coor['index'] == j,'fullname'].values[-1])
        break

    ### for GUI ###

    lat, lon = get_lat_lon(target_place)
      ## need to convert to database's name ##
    
    driver = setup_browser()
    driver.refresh()
    html = driver.page_source
    current_space = find_numbers_between_tags(html)
    distance = [GetDistance(lat, lon, get_lat_lon(i, 'Lat'),get_lat_lon(i, 'Lon')) for i in parking_list]
    parking_order = [[parking_list[i], distance[i], current_space[i]] for i in range(15)]
    parking_order.sort(key=lambda x: x[1])
    for i in parking_order:
        if i[2] > 0:
            print('推薦到', i[0], "停車, 尚有", i[2],"車位", '距離為', round(i[1]*1000, 2), '公尺')
            return 0

#TKinter GUI 程序
class MainApplication(tk.Frame):
    def __init__(self, parent):
        tk.Frame.__init__(self, parent)
        self.parent = parent
        self.create_widgets()

    def create_widgets(self):
        # 輸入校區
        self.campus_label = tk.Label(self, text="請輸入校區：")
        self.campus_label.grid(row=0, column=0, padx=5, pady=5)
        self.campus_input = tk.Entry(self)
        self.campus_input.grid(row=0, column=1, padx=5, pady=5)

        # 輸入系館
        self.department_label = tk.Label(self, text="系館：")
        self.department_label.grid(row=1, column=0, padx=5, pady=5)
        self.department_input = tk.Entry(self)
        self.department_input.grid(row=1, column=1, padx=5, pady=5)

        # 確認及取消按鍵
        self.confirm_button = tk.Button(self, text="確認", command=self.confirm)
        self.confirm_button.grid(row=2, column=0, padx=5, pady=5)

        self.clear_button = tk.Button(self, text="清除", command=self.clear)
        self.clear_button.grid(row=2, column=1, padx=5, pady=5)

    def confirm(self):
        campus_target = self.campus_input.get()
        target_place = self.department_input.get()
        result = main(campus_target, target_place)
        messagebox.showinfo("為您查詢最佳結果", result)

    def clear(self):
        self.campus_input.delete(0, tk.END)
        self.department_input.delete(0, tk.END)


def database():
    # 初始化瀏覽器和資料
    driver = setup_browser()
    
    try:
        while True:
            current_time = time.strftime("%Y-%m-%d %H:%M")
            driver.refresh()
            time.sleep(5)
            html = driver.page_source
            numbers = find_numbers_between_tags(html)
            new_data = pd.DataFrame({'時間': [current_time] * len(parking_list), '停車場名稱': parking_list, '校區': campus_list, '剩餘車位': numbers})
            save_to_excel(new_data)  # 保存數據到 Excel
            print(f"數據更新於 {current_time}，車位剩餘數量：{numbers}")
            time.sleep(55)  # 每60秒更新一次數據，包含刷新後的等待時間
    finally:
        driver.quit()

if __name__ == '__main__':
    root = tk.Tk()
    root.title("校園停車場查訊系統")
    MainApplication(root).pack(expand=True, fill="both")
    root.mainloop()

def getDistance(lat1, lon1, lat2, lon2):

    # 地球半徑，單位是公里
    R = 6371.0

    # 將經緯度從度數轉換為弧度
    lon1 = math.radians(lon1)
    lat1 = math.radians(lat1)
    lon2 = math.radians(lon2)
    lat2 = math.radians(lat2)

    # Haversine 公式
    dlon, dlat = lon2 - lon1, lat2 - lat1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

    # 計算距離
    distance = R * c

    return distance