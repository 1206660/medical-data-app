from flask import Flask, render_template, request, redirect, url_for, send_file
import pandas as pd
import matplotlib.pyplot as plt
import base64
from io import BytesIO
import os

# 设置支持中文的字体
plt.rcParams['font.sans-serif'] = ['SimHei']  # 使用黑体字体，可根据系统更换其他支持中文的字体
plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题

app = Flask(__name__)

# 初始数据
data = {
    '基本信息': {
        '姓名': '沈军',
        '年龄': '65岁',
        '身高': '160cm',
        '体重': '61.5kg'
    },
    '疾病信息': {
        '病理分期': '卵巢癌，高级别，浆液性IIIC期',
        '手术相关': {
            '手术时间': '2019年6月18日',
            '手术范围': '全子宫及右附件切除，右侧卵巢动静脉高位结扎，盆腔及腹主动脉旁淋巴结清扫，大网膜切除，阑尾切除，盆腹腔转移病灶切除，盆腔粘连松解术'
        },
        '病理诊断': '右卵巢及卵巢高级别浆液性癌累及子宫浆膜面及肌层、大网膜、回盲部肿瘤、左侧结肠侧沟肿物、直肠系膜、子宫直肠膈、左侧腹膜、小肠系膜、乙状结肠表面；萎缩性子宫内膜；慢性宫颈及宫颈内膜炎；慢性阑尾炎；多部位淋巴结显慢性炎（右盆腔0/10 ，左盆腔0/12 ，左侧腹主A旁0/7，右腹主A旁0/7）',
        '免疫组化结果': 'CA - 125(+)，PAX - 8(+)，P53(-，无义突变型)，P16(+)，ER(中阳,30%)，PR(中阳,20%)，WT - 1(+)，CK7(+)，CK20(-)，SATB2(局灶+)，HNF1B(-)，NapsinA(-)，Ki - 67(index50%)'
    },
    '病情及肿瘤标志物监测表': [
        {'序号': 1, '检测时间': '2019-05-21', 'CA125（U/ml）': 1834, 'CA153（U/ml）': 97.1, 'CA199（U/ml）': None,
         '时间关键点说明': '首次化疗（一化）前，确立病情初始状态，为化疗方案规划提供基础数据'},
        {'序号': 2, '检测时间': '2019-06-17', 'CA125（U/ml）': 1123, 'CA153（U/ml）': 81.8, 'CA199（U/ml）': None,
         '时间关键点说明': '手术前评估，辅助医生确定手术方案，了解术前肿瘤标志物水平'},
        {'序号': 3, '检测时间': '2019-06-29', 'CA125（U/ml）': 192.1, 'CA153（U/ml）': None, 'CA199（U/ml）': None,
         '时间关键点说明': '第二次化疗（二化）前，评估第一次化疗效果，为二化方案调整提供依据'},
        {'序号': 4, '检测时间': '2019-07-24', 'CA125（U/ml）': 72.9, 'CA153（U/ml）': 22.9, 'CA199（U/ml）': None,
         '时间关键点说明': '第三次化疗（三化）前，依据二化后肿瘤标志物变化，优化三化治疗策略'},
        {'序号': 5, '检测时间': '2019-08-21', 'CA125（U/ml）': 34.3, 'CA153（U/ml）': 28.9, 'CA199（U/ml）': None,
         '时间关键点说明': '第四次化疗（四化）前，查看三化疗效，为后续化疗提供参考'},
        {'序号': 6, '检测时间': '2019-09-12', 'CA125（U/ml）': 26.7, 'CA153（U/ml）': 26.4, 'CA199（U/ml）': None,
         '时间关键点说明': '第五次化疗（五化）前，根据四化结果调整五化用药或方案'},
        {'序号': 7, '检测时间': '2019-10-10', 'CA125（U/ml）': 22.6, 'CA153（U/ml）': None, 'CA199（U/ml）': None,
         '时间关键点说明': '第六次化疗（六化）前，确认五化效果，确定六化最终方案'},
        {'序号': 8, '检测时间': '2019-11-02', 'CA125（U/ml）': 19.6, 'CA153（U/ml）': None, 'CA199（U/ml）': None,
         '时间关键点说明': '六化结束，评估本次化疗对降低肿瘤标志物的成效'},
        {'序号': 9, '检测时间': '2020-01-30', 'CA125（U/ml）': 10.9, 'CA153（U/ml）': None, 'CA199（U/ml）': None,
         '时间关键点说明': '完成六个疗程化疗后3个月，监测化疗后病情稳定情况，排查早期复发风险'},
        {'序号': 10, '检测时间': '2020-05-05', 'CA125（U/ml）': 11.5, 'CA153（U/ml）': None, 'CA199（U/ml）': 12.3,
         '时间关键点说明': '化疗结束6个月，持续追踪病情，通过标志物变化评估恢复状况'},
        {'序号': 11, '检测时间': '2020-08-05', 'CA125（U/ml）': 12.6, 'CA153（U/ml）': None, 'CA199（U/ml）': 12.1,
         '时间关键点说明': '化疗结束9个月，评估病情在较长时间段内的演变趋势'},
        {'序号': 12, '检测时间': '2020-11-05', 'CA125（U/ml）': 14.8, 'CA153（U/ml）': None, 'CA199（U/ml）': 12.6,
         '时间关键点说明': '化疗结束1年，进行年度病情评估，明确化疗长期效果与病情稳定程度'},
        {'序号': 13, '检测时间': '2021-01-11', 'CA125（U/ml）': 23.3, 'CA153（U/ml）': 24, 'CA199（U/ml）': 13.5,
         '时间关键点说明': '化疗结束1年2个月，定期复查，及时发现病情潜在波动'},
        {'序号': 14, '检测时间': '2021-01-30', 'CA125（U/ml）': 28.9, 'CA153（U/ml）': 24.8, 'CA199（U/ml）': 13.1,
         '时间关键点说明': '化疗结束1年3个月，再次复查，持续关注病情动态'},
        {'序号': 15, '检测时间': '2021-02-25', 'CA125（U/ml）': 12.2, 'CA153（U/ml）': 24.8, 'CA199（U/ml）': 13.5,
         '时间关键点说明': '化疗结束1年3个月且安罗替尼 + 尼拉帕利联合治疗1个月后，评估新方案初步疗效'},
        {'序号': 16, '检测时间': '2021-04-21', 'CA125（U/ml）': 8.52, 'CA153（U/ml）': None, 'CA199（U/ml）': 14.47,
         '时间关键点说明': '化疗结束1年5个月，联合治疗2个半月后，进一步观察新方案对病情的影响'},
        {'序号': 17, '检测时间': '2021-05-09', 'CA125（U/ml）': 14.93, 'CA153（U/ml）': None, 'CA199（U/ml）': 14.61,
         '时间关键点说明': '化疗结束1年7个月，联合治疗3个月且因副作用暂停安罗替尼期间，评估该特殊阶段病情变化'},
        {'序号': 18, '检测时间': '2021-06-24', 'CA125（U/ml）': 8.6, 'CA153（U/ml）': None, 'CA199（U/ml）': 14.5,
         '时间关键点说明': '化疗结束1年7个月，持续监测新方案下病情及标志物变化情况'},
        {'序号': 19, '检测时间': '2021-08-02', 'CA125（U/ml）': 12, 'CA153（U/ml）': 25.7, 'CA199（U/ml）': 14.1,
         '时间关键点说明': '化疗结束1年9个月，定期评估新方案长期疗效与病情稳定性'},
        {'序号': 20, '检测时间': '2021-09-11', 'CA125（U/ml）': 9.2, 'CA153（U/ml）': 27.8, 'CA199（U/ml）': 14.7,
         '时间关键点说明': '化疗结束1年10个月，持续追踪新方案效果与病情变化趋势'},
        {'序号': 21, '检测时间': '2021-10-31', 'CA125（U/ml）': 11.1, 'CA153（U/ml）': 24, 'CA199（U/ml）': 15.8,
         '时间关键点说明': '化疗结束2年，进行两年病情总结评估，判断新方案长期效果与病情走向'},
        {'序号': 22, '检测时间': '2021-12-05', 'CA125（U/ml）': 20.9, 'CA153（U/ml）': None, 'CA199（U/ml）': 16.5,
         '时间关键点说明': '化疗结束2年1个月，定期复查，留意病情细微变化'},
        {'序号': 23, '检测时间': '2021-12-16', 'CA125（U/ml）': 10.8, 'CA153（U/ml）': 23.1, 'CA199（U/ml）': 16,
         '时间关键点说明': '化疗结束2年1个月，再次复查确保及时发现病情异常'},
        {'序号': 24, '检测时间': '2022-02-10', 'CA125（U/ml）': 22.7, 'CA153（U/ml）': 24.4, 'CA199（U/ml）': 14.5,
         '时间关键点说明': '化疗结束2年3个月，定期监测新方案持续效果'},
        {'序号': 25, '检测时间': '2022-04-29', 'CA125（U/ml）': 14.4, 'CA153（U/ml）': None, 'CA199（U/ml）': 15.9,
         '时间关键点说明': '化疗结束2年6个月，半年期复查全面评估病情与新方案疗效'},
        {'序号': 26, '检测时间': '2022-08-05', 'CA125（U/ml）': 22.3, 'CA153（U/ml）': 28, 'CA199（U/ml）': 16.5,
         '时间关键点说明': '化疗结束2年9个月，持续关注病情及新方案下标志物变化'},
        {'序号': 27, '检测时间': '2023-05-13', 'CA125（U/ml）': 8.7, 'CA153（U/ml）': None, 'CA199（U/ml）': None,
         '时间关键点说明': '复发结疗后首次复查（距离2023.4.30结疗约13天），评估结疗后早期病情状况'},
        {'序号': 28, '检测时间': '2023-07-13', 'CA125（U/ml）': 9.0, 'CA153（U/ml）': 25.5, 'CA199（U/ml）': 16.7,
         '时间关键点说明': '复发结疗后约2个半月复查，持续监测病情变化'},
        {'序号': 29, '检测时间': '2023-08-26', 'CA125（U/ml）': 8.6, 'CA153（U/ml）': None, 'CA199（U/ml）': None,
         '时间关键点说明': '复发结疗后约4个月复查，观察病情及标志物动态'},
        {'序号': 30, '检测时间': '2023-09-12', 'CA125（U/ml）': 9.1, 'CA153（U/ml）': None, 'CA199（U/ml）': None,
         '时间关键点说明': '复发结疗后约4个半月复查，定期跟踪病情'},
        {'序号': 31, '检测时间': '2023-10-04', 'CA125（U/ml）': 8.3, 'CA153（U/ml）': None, 'CA199（U/ml）': None,
         '时间关键点说明': '复发结疗后约5个月复查，确保病情处于可控状态'},
        {'序号': 32, '检测时间': '2023-12-07', 'CA125（U/ml）': 8.5, 'CA153（U/ml）': 22.9, 'CA199（U/ml）': None,
         '时间关键点说明': '复发结疗后约7个半月复查，评估病情及标志物水平'},
        {'序号': 33, '检测时间': '2023-12-27', 'CA125（U/ml）': 9.5, 'CA153（U/ml）': 25.9, 'CA199（U/ml）': 14.2,
         '时间关键点说明': '复发结疗后约8个月复查，年末全面了解病情'},
        {'序号': 34, '检测时间': '2024-01-18', 'CA125（U/ml）': 8.8, 'CA153（U/ml）': 25.0, 'CA199（U/ml）': 16.2,
         '时间关键点说明': '复发结疗后约9个月复查，年初为新一年病情管理提供数据'},
        {'序号': 35, '检测时间': '2024-05-29', 'CA125（U/ml）': 14.8, 'CA153（U/ml）': 23.6, 'CA199（U/ml）': 15.4,
         '时间关键点说明': '复发结疗后约13个月复查，进行年度病情评估'},
        {'序号': 36, '检测时间': '2024-07-16', 'CA125（U/ml）': 23.5, 'CA153（U/ml）': 23.0, 'CA199（U/ml）': 15.0,
         '时间关键点说明': '复发结疗后约14个半月复查，监测病情发展态势'},
        {'序号': 37, '检测时间': '2024-08-22', 'CA125（U/ml）': 6.7, 'CA153（U/ml）': None, 'CA199（U/ml）': None,
         '时间关键点说明': '复发结疗后约16个月复查，观察CA125变化判断病情'},
        {'序号': 38, '检测时间': '2024-10-11', 'CA125（U/ml）': 9.9, 'CA153（U/ml）': 37.6, 'CA199（U/ml）': 18.0,
         '时间关键点说明': '复发结疗后约17个半月复查，全面了解标志物水平判断病情'},
        {'序号': 39, '检测时间': '2024-10-14', 'CA125（U/ml）': 11.7, 'CA153（U/ml）': 23.8, 'CA199（U/ml）': 17.1,
         '时间关键点说明': '复发结疗后约17个半月复查（与上条时间相近，综合评估病情变化）'},
        {'序号': 40, '检测时间': '2024-12-23', 'CA125（U/ml）': 12.0, 'CA153（U/ml）': 26.2, 'CA199（U/ml）': None,
         '时间关键点说明': '复发结疗后约20个月复查，关注标志物为后续治疗提供依据'},
        {'序号': 41, '检测时间': '2025-01-08', 'CA125（U/ml）': 12.0, 'CA153（U/ml）': 26.2, 'CA199（U/ml）': None,
         '时间关键点说明': '复发结疗后约20个半月复查，年初评估病情开启新一年监测'},
        {'序号': 42, '检测时间': '2025-03-19', 'CA125（U/ml）': 11.7, 'CA153（U/ml）': 23.8, 'CA199（U/ml）': 17.1,
         '时间关键点说明': '复发结疗后约23个月复查，持续跟踪病情评估长期疗效'}
    ]
}


def generate_plot(data):
    df = pd.DataFrame(data['病情及肿瘤标志物监测表'])
    df['检测时间'] = pd.to_datetime(df['检测时间'])
    marker_norms = {
        'CA125（U/ml）': 35,
        'CA153（U/ml）': 34,
        'CA199（U/ml）': 16.7
    }
    plot_urls = []
    filenames = []
    for marker in ['CA125（U/ml）', 'CA153（U/ml）', 'CA199（U/ml）']:
        non_na_mask = df[marker].notna()
        x = df['检测时间'][non_na_mask]
        y = df[marker][non_na_mask]

        num_plots = (len(x) + 11) // 12
        for i in range(num_plots):
            start_idx = i * 12
            end_idx = start_idx + 12
            x_subset = x[start_idx:end_idx]
            y_subset = y[start_idx:end_idx]

            plt.figure(figsize=(12, 6))
            # 转换为等间距的索引
            x_index = range(len(x_subset))
            # 去掉平滑处理
            plt.plot(x_index, y_subset, label=marker)
            # 绘制正常值参考线
            plt.axhline(y=marker_norms[marker], color='r', linestyle='--', label=f'{marker} 正常值')

            # 标注每个时间点的数值，保留1位小数
            for xi, yi in zip(x_index, y_subset):
                color = 'red' if yi >= marker_norms[marker] else 'green'
                # 处理超出最大值的情况
                if yi > marker_norms[marker] * 2:
                    y_display = marker_norms[marker] * 2
                else:
                    y_display = yi
                plt.annotate(f'{yi:.1f}', (xi, y_display), textcoords="offset points",
                             xytext=(0, 10), ha='center', color=color)

            plt.xlabel('检测时间')
            plt.ylabel('指标值')
            if num_plots > 1:
                plt.title(f'{marker} 随时间变化曲线（第 {i + 1} 部分）')
            else:
                plt.title(f'{marker} 随时间变化曲线')
            # 设置 y 轴范围为 0 到该标志物正常值的 2 倍
            plt.ylim(0, marker_norms[marker] * 2)
            # 设置 x 轴标签为原来的日期，只显示年月
            plt.xticks(x_index, x_subset.dt.strftime('%Y-%m'), rotation=0, ha='center')
            plt.legend()
            plt.grid(True)

            # 在右上角添加正常值说明
            norm_text = f'{marker} <= {marker_norms[marker]}'
            plt.text(0.95, 0.95, norm_text, horizontalalignment='right', verticalalignment='top',
                     transform=plt.gca().transAxes, bbox=dict(facecolor='white', alpha=0.7))

            img = BytesIO()
            plt.savefig(img, format='png')
            img.seek(0)
            plot_url = base64.b64encode(img.getvalue()).decode()
            plot_urls.append(plot_url)
            # 生成文件名
            if len(x_subset) > 0:
                year = x_subset.min().year
            else:
                year = 'unknown'
            filename = f'{marker}_{year}.png'
            filenames.append(filename)
            plt.close()
    return plot_urls, filenames


@app.route('/')
def index():
    plot_urls, filenames = generate_plot(data)
    return render_template('index.html', data=data, plot_urls=plot_urls, filenames=filenames)


@app.route('/add_data', methods=['GET', 'POST'])
def add_data():
    if request.method == 'POST':
        new_data = {
            '序号': len(data['病情及肿瘤标志物监测表']) + 1,
            '检测时间': request.form.get('检测时间'),
            'CA125（U/ml）': float(request.form.get('CA125（U/ml）')),
            'CA153（U/ml）': float(request.form.get('CA153（U/ml）')),
            'CA199（U/ml）': float(request.form.get('CA199（U/ml）')),
            '时间关键点说明': request.form.get('时间关键点说明')
        }
        data['病情及肿瘤标志物监测表'].append(new_data)
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
    