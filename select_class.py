import requests
from bs4 import BeautifulSoup
import re
import time
from configparser import ConfigParser
import random

def query_class(cf, could_not_get_table, info_all=True):
	'''
	查询选课

	Args:
		cf: 配置文件解析出来的键值对
		could_not_get_table: 不能获取选课表格的次数，超过一定次数，返回1，让主程序报错，退出死循环
		info_all: 是否通知所有消息

	Returns:
		0表示函数还可继续循环运行，否则返回1
	'''
	# 服务器ip地址
	# host_url = 'http://10.3.255.3x'
	host_url = cf.get('script', 'host_url')
	url = host_url + '/Lesson/PlanCourseOnlineSel.aspx'

	#请求头信息，注意Cookie使用你登录时的cookie，详见README.md，User-Agent的值一般不用动
	cookie = cf.get('script', 'cookie')
	# head={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.138 Safari/537.36', 'Cookie': 'ASP.NET_SessionId=xxxxxxxxxxxxxxxx; DropDownListYx_xsbh=xxxxxx; DropDownListXqu='}
	head={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.138 Safari/537.36', 'Cookie': cookie}
	# 向url发送GET请求
	html = requests.get(url, headers=head)
	html.encoding='utf-8'
	# with open('test.html', 'w', encoding='utf-8') as f:
	#     f.write(html.text)
	# input()
	# 装配html解析器
	soup = BeautifulSoup(html.text, 'lxml')
	# 找到选课的表格
	table = soup.find('table', {'class': 'Grid_Line'})
	if not table:
		print('获取不到选课表格，请换一个新的cookie证明登陆身份')
		# 获取不到表格连续超过5次，报cookie无效的错
		if could_not_get_table > 5:
			return 1
		could_not_get_table+=1
		return 0	
	elif could_not_get_table > 0:
		could_not_get_table -= 1
	# print(table)
	# input()
	# class_dict = {}
	# 你想选的课的名称
	# the_disired_class_names = ['自然辩证法概论', '研究生英语职场交流', '研究生英语国际会议交流', '研究生英语公共演讲', '研究生英语跨文化交流', '研究生英语学术听说', '研究生英语学术写作', '中国特色社会主义理论与实践研究', '软件开发项目管理(MOOC)']
	# 从配置文件中获取课程名列表字符串
	disired_class_names = cf.get('script', 'desired_class_names')[1:-1]
	the_disired_class_names = ','.join(disired_class_names.split(','))
	# print(type(the_disired_class_names), the_disired_class_names)
	# the_disired_class_names = ['软件确保']
	# 将一个数据行的数据一个元素一个元素地找出放入列表中
	for tr in table.findAll('tr'):
		# 判断该数据行的课程名是否为想要的课程名
		desired_row = True
		tds = []
		# 分析单元格的内容
		for idx, td in enumerate(tr.findAll('td')):
			# 找课程名
			if idx == 1:
				# print(td.getText().strip())
				if td.getText().strip() not in the_disired_class_names:
					desired_row = False
					break
			td_text = td.getText().strip()
			# print(td_text.strip())
			tds.append(td_text)
		# 分析的数据行不是想要的课程
		if not desired_row:
			continue	
		# print(tds)
		# print()
		# 该数据行没有内容就分析下一个数据行
		if len(tds) != 11:
			continue
		# 该数据行有想要的课程
		if tds[1] in the_disired_class_names:
			# print(tds[1])
			if info_all:
				print('考察%s的选课情况'%tds[1], end=',')
			# 如果可以选课
			if tds[-4] == '选择上课班级':
				if info_all:
					print('准备选课')
				# 找选课按钮这个元素
				could_sel_a = tr.find(name='a', attrs={'id': re.compile(r'contentParent_dgData_hykSelkc_\d+')})
				# print(could_sel_a)
				# if could_sel_a is None:
				# 	continue
				# print(could_sel_a.attrs['onclick'][10:-14])
				# 根据按钮的onclick属性值获取选课对话框的url
				select_dialog_url = host_url + '/Gstudent/Course/PlanSelClass.aspx' + could_sel_a.attrs['onclick'][10:-14]
				# 向选课对话框url发送URL请求
				select_dialog_html = requests.get(select_dialog_url,headers=head)
				select_dialog_html.encoding = 'utf-8'
				# print(select_dialog_html.text)
				# input() 
				select_dialog_soup = BeautifulSoup(select_dialog_html.text, 'lxml')
				# 找到隐藏的input标签，准备将属性值放入表单中
				inputs = select_dialog_soup.findAll('input')
				# print(inputs)
				# 表单字典
				data = {}
				for inpu in inputs:
					if inpu.attrs['type'] == 'hidden':
						data[inpu.attrs['name']] = inpu.attrs['value']
				# 从浏览器检查的网络中看到的其他表单项，不清楚这些表单项的作用，但不能没有这些
				data['ctl00$ScriptManager1'] = 'ctl00$contentParent$UpdatePanel2|ctl00$contentParent$dgData$ctl02$ImageButton1'
				data['ctl00$contentParent$drpXqu$drpXqu'] = ''
				data['__ASYNCPOST'] = 'true'
				data['ctl00$contentParent$dgData$ctl02$ImageButton1.x'] = '6'
				data['ctl00$contentParent$dgData$ctl02$ImageButton1.y'] = '3'
				# 向选课URL发送POST请求
				to_select = requests.post(select_dialog_url, data, headers=head)
				to_select.encoding = 'utf-8'
				print('可能选中 %s 课，请到系统中查看'%tds[1])
				# print(data)
				# print(to_select.text)
				# input()
			else:
				print('无法选课')

if __name__ == '__main__':
	# 获取不到选课表格的次数
	could_not_get_table = 0
	# 统计请求次数
	count = 0
	# 读配置文件
	cf = ConfigParser()
	cf.read('config.ini', encoding='utf-8')
	# 是否通知所有消息
	# info_all = True
	info_all = cf.getboolean('script', 'info_all')
	# print(type(info_all))
	while(True):
		# 爬虫爬取的时间间隔
		sleep_time = 5 + random.randint(0, 10)
		if info_all:
			print('第%d次请求选课，%d秒后会再次请求'%(count, sleep_time))
		count+=1
		# 脚本查询选课
		ret = query_class(cf, could_not_get_table, info_all)
		time.sleep(sleep_time)
		# 如果返回值为1，说明cookie失效，需要重新登陆
		if ret == 1:
			break
