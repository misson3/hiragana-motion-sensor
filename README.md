# hiragana-motion-sensor
Mar11, 2023

実験的webの記事、[モーションセンサーでひらがな認識](https://makeintoshape.com/acc-gyr-hiragana)　で使ったコードたちです。



**acc-gyr-Reader-v1.ino**

Microcontrolerにのせて使う、センサー読み取り用のArduinoコードです。

Adafruit QT Pyにのせて使いました。LSM6DSOXからの読み取り値を "," 区切りでserialへ送出します。accelerometerからのx, y, z, gyroscopeからのx, y, zに続いて、タッチセンサーとして使っているA1（ペンタッチ用）, A3（プログラム終了用シグナル）の読み取り値の順です。



**serialRecorder-touch-robust2.py**

トレーニングデータを集めていくために使うコードです。

USBに読み取りデバイスをつなぎ、このプログラムを走らせます。ペンがタッチされている一続きの間のデータが一つのファイルに保存されていきます。一つのひらがなにつき、走らせていきます。例えば「あ」のデータを取る場合、

```bash
python serialRecorder-touch-robust2.py a
```

のようにして"a"をargとして与えると、

```bash
a-001.csv
a-002.csv
...
```

のように与えたargの文字を冠した連番のcsvファイルがcurrent dirに保存されていきます。QT PyのA3につないだパッドにタッチするとプログラムが終了します。

ファイルの頭から最初のハイフンまでの文字が、この後の処理でラベルとして用いられます。



**tail-chopper.py**

上のcsvファイルに含まれる（不必要な）最後の数行を削除するためのコードです。

記事に書きましたが、上のコードでは一筆書き中に起こる短い途切れ（パッドから離れたと判定される瞬間）をある程度許容するように対策しています。そのため、文字を書き終わった後の短い期間分の読み取り値もファイルに含まれてしまいます。その部分のデータ行をcsvから削除するコードです。

最初からserialRecoder codeでやっとけよ、という操作なのですが、大量のデータを取り終わったあとに、この部分を取り除いた方がモデルの成績が良くなることに気が付いてしまい、楽な方法に逃げてしまった故のコードです。もしこのプロジェクトをお試しになる場合には、tail choppingを読み取りコードのほうに取り込んでしまうことをお勧めします。

使い方は以下の通りで、csvの入ったdirectoryをargとして与えてください。"-no-tail"というpostfixのついたファイルがcurrent dirにできてきます。

```bash
python tail-chopper.py <csv dir>
```



**conv2d-train.ipynb**

modelの構築に使ったjupyter noteです。

model file（.h5）、出力nodeのindexとラベルとを対応させるためのpython dictをpklファイルとしたものとが保存されます。ファイル名にはtime stampをはじめbatch size, epoc数, validation dataの正解率とおまけに畳み関連のパラメターまで含むようにしてあるので、ものすごく長いです。これはあれこれ繰り返し試したときにファイルを区別することができるようにするためのものなので、必要ない場合にはもっと簡単なファイル名になるようにしてください。



 **model-tester-CNN-3.py**

modelを使ってみるためのcodeです。h5 file, pkl fileの順にpathを与えてください。

```bash
python model-tester-CNN3.py <path to h5 file> <path to pkl file>
```



**filter-viewer.py**

trainingの結果得られた畳み込みファイルと、それをデータに当てはめた前後の結果を描画する、ちょっと面白いコードです。

二つのデータを扱うようになっています。流し込みたいcsvファイル二つをフォルダに入れて準備してください。フィルタ数は4であるとしてhard codeしてあります。

model fileへのpathと、二つのcsvファイルの入ったフォルダへのpathを与えて使います。

```bash
python filter-viewer.py <path to h5 file> <path to the csv dir>
```



**conda-list-tf2.txt**

用いたconda env (tf2)からの、conda listの結果を保存しておきました。tensorflowやnumpyのバージョンをみることができます。


