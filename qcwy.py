from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import time
import pymysql
import requests
from lxml import etree


class QCWY:
    data_list = []

    def __init__(self, keyword, city, max_pagenum):
        self.keyword = keyword
        self.city = city
        self.max_pagenum = max_pagenum


    def run(self):
        driver = webdriver.Chrome(executable_path='chromedriver.exe')
        driver.implicitly_wait(10)
        # 选择网站
        driver.get('https://www.51job.com/')
        # 定位坐标
        kw_input = driver.find_element_by_id('kwdselectid')
        # 输入搜索内容
        kw_input.send_keys(self.keyword)
        # 定位城市
        driver.find_element_by_id('work_position_input').click()
        time.sleep(1)
        # 选择城市,点击上方当前已经选择的城市,去掉
        selectedCityEles = driver.find_elements_by_css_selector('#work_position_click_multiple_selected > span')
        for one in selectedCityEles:
            one.click()

        # 然后选择我们的城市
        cityeles = driver.find_elements_by_css_selector('#work_position_click_center_right_list_000000 em')
        target = None
        for i in cityeles:
            if i.text == self.city:
                target = i
                break

        # 没有找到该名称的城市
        if target is None:
            input(f'{self.city} 不在热门城市列表,请手动点击选中城市,')
        else:
            target.click()

        # 保存城市
        driver.find_element_by_id('work_position_click_bottom_save').click()

        # 点击搜索
        driver.find_element_by_css_selector('div.ush > button').click()

        for page in range(1, self.max_pagenum + 1):
            # 设置页码
            page_input = driver.find_element_by_id('jump_page')
            page_input.clear()
            page_input.send_keys(str(page))
            driver.find_element_by_class_name('og_but').click()
            # 起稳定作用
            time.sleep(1)
            self.handleOnePage(driver)
            # 是否到了最后一页
            if self.islastPage(driver):
                self.save_mysql_data()
                break

    def islastPage(self, driver):
        # 获取class 值  最后一页的值为 bk next  其他为next
        nextpagebutton = driver.find_element_by_css_selector('div.p_in li:last-child').get_attribute('class')
        if nextpagebutton == 'next':
            return False
        return True

    def handleOnePage(self, driver):
        # 处理每页信息
        jobs = driver.find_elements_by_css_selector('div[class="j_joblist"] > div')
        for job in jobs:
            # 岗位名称
            jname = job.find_element_by_class_name('jname').text
            # 公司名称
            cname = job.find_element_by_class_name('cname').text
            # 工资待遇
            gongzhi = job.find_element_by_class_name('sal').text
            # 上班地点
            didian = job.find_element_by_class_name('d').text
            # 公司类型
            leixing = job.find_element_by_class_name('int').text
            # 公司规模
            guimo = job.find_element_by_class_name('dc').text
            # 详细说明链接
            herf_url = job.find_element_by_class_name('el').get_attribute('href')
            data_dict = {
                'jname': jname,
                'cname': cname,
                'gongzhi': gongzhi,
                'didian': didian,
                'leixing': leixing,
                'guimo': guimo,
                'herf_url': herf_url,
            }
            headers = {
                'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.14 Safari/537.36'
            }
            page = requests.get(url=herf_url,headers=headers)
            page.encoding = 'gbk'
            tree = etree.HTML(page.text)
            msg = tree.xpath('/html/body/div[3]/div[2]/div[3]/div[1]/div//text()')
            msg = ''.join(msg)
            data_dict['work_msg'] = msg
            # 点击打开链接
            # job.find_element_by_class_name('el').click()
            # mainwindow 变量保存当前窗口的句柄
            # mainWindow = driver.current_window_handle
            # 新打开的窗口总是句柄列表中的最后一个
            # driver.switch_to.window(driver.window_handles[-1])

            # info = driver.find_elements_by_css_selector('.tCompany_main .job_msg')
            # if info and len(info) == 1:
            #     work_msg = info[0].text
            #     data_dict['work_msg'] = work_msg
            # 关闭具体信息页
            # driver.close()
            # 通过前面保存的老窗口的句柄,自己切换到老窗口
            # driver.switch_to.window(mainWindow)
            self.save_data(data_dict)

    def save_data(self, data):
        data_tuple = (
            data['jname'], data['cname'], data['gongzhi'], data['didian'], data['leixing'], data['guimo'],
            data['herf_url'],
            data.get('work_msg'))
        self.data_list.append(data_tuple)

    def save_mysql_data(self):
        print(self.data_list)
        conn = pymysql.connect(
            host='127.0.0.1',
            user='root',
            password='123',
            database='spidernew'
        )
        cursor = conn.cursor(cursor=pymysql.cursors.DictCursor)
        try:
            # 定义要执行的SQL语句
            sql = """
                insert into qcwu values ("%s","%s","%s","%s","%s","%s","%s","%s")
            """

            # 执行SQL语句
            cursor.executemany(sql, self.data_list)
            conn.commit()
        except Exception:
            conn.rollback()


if __name__ == '__main__':
    objs = QCWY('python爬虫', '深圳', 2)
    objs.run()

