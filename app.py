from flask import Flask, render_template, request, redirect, url_for, send_file
import pandas as pd
import matplotlib.pyplot as plt
import base64
from io import BytesIO
import os
import json

# 设置支持中文的字体
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

app = Flask(__name__)


# 从JSON文件读取数据
try:
    with open('patient_info.json', 'r', encoding='utf-8') as file:
        data = json.load(file)
except FileNotFoundError:
    print("未找到 patient_info.json 文件，请检查文件是否存在。")
    data = {}
except json.JSONDecodeError:
    print("解析 patient_info.json 文件时出错，请检查文件内容格式。")
    data = {}


def generate_plot(data):
    """
    该函数用于生成肿瘤标志物随时间变化的曲线图，并返回图像的Base64编码列表和对应的文件名列表。

    参数:
    data (dict): 包含患者病情及肿瘤标志物监测表的字典数据。

    返回:
    tuple: 包含两个列表，第一个列表是图像的Base64编码字符串，第二个列表是对应的文件名。
    """
    # 将病情及肿瘤标志物监测表数据转换为DataFrame
    df = pd.DataFrame(data['病情及肿瘤标志物监测表'])
    # 将检测时间列转换为日期时间类型
    df['检测时间'] = pd.to_datetime(df['检测时间'])
    # 定义肿瘤标志物的正常值
    marker_norms = {
        'CA125（U/ml）': 35,
        'CA153（U/ml）': 34,
        'CA199（U/ml）': 16.7
    }
    plot_urls = []
    filenames = []
    # 遍历每个肿瘤标志物
    for marker in ['CA125（U/ml）', 'CA153（U/ml）', 'CA199（U/ml）']:
        # 筛选出该标志物非缺失值的数据
        non_na_mask = df[marker].notna()
        x = df['检测时间'][non_na_mask]
        y = df[marker][non_na_mask]
        important_marks = df.loc[non_na_mask, '重要标记']

        # 计算需要绘制的子图数量，每12个数据点绘制一个子图
        num_plots = (len(x) + 11) // 12
        for i in range(num_plots):
            start_idx = i * 12
            end_idx = start_idx + 12
            # 截取当前子图的数据
            x_subset = x[start_idx:end_idx]
            y_subset = y[start_idx:end_idx]
            important_marks_subset = important_marks[start_idx:end_idx]

            # 创建一个新的图形
            plt.figure(figsize=(12, 6))
            # 生成x轴的索引
            x_index = range(len(x_subset))
            # 绘制肿瘤标志物随时间变化的曲线
            plt.plot(x_index, y_subset, label=marker)
            # 绘制该标志物的正常值水平线
            plt.axhline(y=marker_norms[marker], color='r', linestyle='--', label=f'{marker} 标准阈值 <= {marker_norms[marker]}')

            # 为每个数据点添加注释
            for xi, yi in zip(x_index, y_subset):
                color = 'red' if yi >= marker_norms[marker] else 'green'
                if yi > marker_norms[marker] * 2:
                    y_display = marker_norms[marker] * 2
                else:
                    y_display = yi
                plt.annotate(f'{yi:.1f}', (xi, y_display), textcoords="offset points",
                             xytext=(0, 10), ha='center', color=color)

            # 设置x轴和y轴的标签
            plt.xlabel('检测时间')
            plt.ylabel('指标值')
            # 根据子图数量设置标题，包含标准值
            if num_plots > 1:
                plt.title(f'{marker} 随时间变化（第 {i + 1} 部分），标准值: {marker_norms[marker]}')
            else:
                plt.title(f'{marker} 随时间变化，标准值: {marker_norms[marker]}')
            # 设置y轴的范围
            plt.ylim(0, marker_norms[marker] * 2)
            # 设置x轴的刻度标签
            plt.xticks(x_index, x_subset.dt.strftime('%Y-%m'), rotation=0, ha='center')
            # 显示图例
            plt.legend()
            # 显示网格线
            plt.grid(True)

            # 显示该标志物的正常值注释，设置半透明背景
            # norm_text = f'标准值 <= {marker_norms[marker]}'
            # plt.text(1, 1, norm_text, horizontalalignment='left', verticalalignment='top',
            #          transform=plt.gca().transAxes, fontsize=12, color='black',
            #          bbox=dict(facecolor='white', edgecolor='black', boxstyle='round,pad=0.3', alpha=0.7))

            # 突出标记重要信息
            for xi, mark in zip(x_index, important_marks_subset):
                #if pd.notna(mark):
                if mark != None:
                    y_val = y_subset.iloc[xi]
                    plt.annotate(mark,
                                 xy=(xi, y_val + 5),
                                 xytext=(xi, y_val + 10),
                                 arrowprops=dict(facecolor='red', shrink=0.05),
                                 fontsize=16, color='red', ha='center', va='bottom')

            # 将图像保存到内存中的BytesIO对象
            img = BytesIO()
            plt.savefig(img, format='png')
            img.seek(0)
            # 将图像数据进行Base64编码
            plot_url = base64.b64encode(img.getvalue()).decode()
            plot_urls.append(plot_url)
            if len(x_subset) > 0:
                year = x_subset.min().year
            else:
                year = 'unknown'
            filename = f'{marker}_{year}.png'
            filenames.append(filename)
            # 关闭当前图形
            plt.close()
    return plot_urls, filenames


@app.route('/')
def index():
    plot_urls, filenames = generate_plot(data)
    zipped_data = list(zip(plot_urls, filenames))
    return render_template('index.html', data=data, zipped_data=zipped_data)


@app.route('/add_data', methods=['GET', 'POST'])
def add_data():
    if request.method == 'POST':
        new_data = {
            '序号': len(data['病情及肿瘤标志物监测表']) + 1,
            '检测时间': request.form.get('检测时间'),
            'CA125（U/ml）': float(request.form.get('CA125（U/ml）')),
            'CA153（U/ml）': float(request.form.get('CA153（U/ml）')),
            'CA199（U/ml）': float(request.form.get('CA199（U/ml）')),
            '时间关键点说明': request.form.get('时间关键点说明'),
            '重要标记': request.form.get('重要标记')
        }
        data['病情及肿瘤标志物监测表'].append(new_data)
        try:
            with open('patient_info.json', 'w', encoding='utf-8') as file:
                json.dump(data, file, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"保存数据到JSON文件时出错: {e}")
        return redirect(url_for('index'))
    return render_template('add_data.html')


@app.route('/download_all_images')
def download_all_images():
    import zipfile
    import io

    memory_file = io.BytesIO()
    with zipfile.ZipFile(memory_file, 'w') as zf:
        plot_urls, filenames = generate_plot(data)
        for plot_url, filename in zip(plot_urls, filenames):
            img_data = base64.b64decode(plot_url)
            zf.writestr(filename, img_data)
    memory_file.seek(0)
    return send_file(
        memory_file,
        as_attachment=True,
        download_name='all_images.zip',
        mimetype='application/zip'
    )


if __name__ == '__main__':
    app.run(debug=True)
    