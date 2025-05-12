import 'dart:async';
import 'package:flutter/material.dart';
import 'package:sensors_plus/sensors_plus.dart';
import 'package:logging/logging.dart';
import 'package:flutter/foundation.dart' show kIsWeb;
import 'package:vibration/vibration.dart';
import 'package:audioplayers/audioplayers.dart';
import 'package:shared_preferences/shared_preferences.dart';

// ロガーを設定
final Logger logger = Logger('GyroscopeApp');

// アプリ全体でテーマモードを管理するクラス
class ThemeProvider extends ChangeNotifier {
  ThemeMode _themeMode = ThemeMode.dark;

  ThemeMode get themeMode => _themeMode;

  void toggleTheme() {
    _themeMode =
        _themeMode == ThemeMode.light ? ThemeMode.dark : ThemeMode.light;
    notifyListeners();
  }
}

void main() {
  runApp(const MyApp());
}

class MyApp extends StatefulWidget {
  const MyApp({super.key});

  @override
  State<MyApp> createState() => _MyAppState();
}

class _MyAppState extends State<MyApp> {
  final ThemeProvider _themeProvider = ThemeProvider();

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
        animation: _themeProvider,
        builder: (context, child) {
          return MaterialApp(
            title: '腹筋トレーニング',
            theme: ThemeData(
              colorScheme: ColorScheme.fromSeed(
                seedColor: Colors.blue,
                brightness: Brightness.light,
              ),
              useMaterial3: true,
              cardTheme: CardTheme(
                elevation: 6,
                shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(16)),
              ),
              appBarTheme: const AppBarTheme(
                elevation: 0,
                centerTitle: true,
              ),
            ),
            darkTheme: ThemeData(
              colorScheme: ColorScheme.fromSeed(
                seedColor: Colors.indigo,
                brightness: Brightness.dark,
              ),
              useMaterial3: true,
              cardTheme: CardTheme(
                elevation: 6,
                shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(16)),
              ),
              appBarTheme: const AppBarTheme(
                elevation: 0,
                centerTitle: true,
              ),
            ),
            themeMode: _themeProvider.themeMode,
            home: BallPage(themeProvider: _themeProvider),
          );
        });
  }
}

class BallPage extends StatefulWidget {
  final ThemeProvider themeProvider;

  const BallPage({super.key, required this.themeProvider});

  @override
  State<BallPage> createState() => _BallPageState();
}

class _BallPageState extends State<BallPage>
    with SingleTickerProviderStateMixin {
  double ballPosition = 0.5;
  int counter = 0;
  int targetCount = 10;
  Map<int, double> axisSensitivity = {
    0: 0.15,
    1: 0.01,
    2: 0.03,
  };
  bool invertAxis = false;
  int selectedAxis = 0;
  String axisNames = "XYZ";
  StreamSubscription<GyroscopeEvent>? _gyroSub;

  bool reachedTop = false;
  bool reachedBottom = true;

  bool canVibrate = false;
  DateTime? lastVibration;

  double gyroX = 0.0;
  double gyroY = 0.0;
  double gyroZ = 0.0;
  bool sensorAvailable = false;

  late AnimationController _animationController;
  late Animation<double> _backgroundAnimation;

  final AudioPlayer _audioPlayer = AudioPlayer();
  bool _isPlaying = false;

  @override
  void initState() {
    super.initState();

    _loadTargetCount();

    _audioPlayer.onPlayerStateChanged.listen((PlayerState state) {
      setState(() {
        _isPlaying = state == PlayerState.playing;
      });
    });

    _animationController = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 3),
    )..repeat(reverse: true);

    _backgroundAnimation =
        Tween<double>(begin: 0.0, end: 1.0).animate(_animationController);

    _checkVibrationSupport();

    try {
      _gyroSub = gyroscopeEventStream().listen((GyroscopeEvent event) {
        setState(() {
          gyroX = event.x;
          gyroY = event.y;
          gyroZ = event.z;
          sensorAvailable = true;

          double previousPosition = ballPosition;

          double axisValue = 0;
          switch (selectedAxis) {
            case 0:
              axisValue = event.x;
              break;
            case 1:
              axisValue = event.y;
              break;
            case 2:
              axisValue = event.z;
              break;
          }

          if (invertAxis) {
            axisValue = -axisValue;
          }

          double currentSensitivity = axisSensitivity[selectedAxis] ?? 0.015;

          ballPosition -= axisValue * currentSensitivity;
          if (ballPosition < 0) ballPosition = 0;
          if (ballPosition > 1) ballPosition = 1;

          if (ballPosition <= 0.0 && previousPosition > 0.0) {
            _vibrateIfNeeded();

            if (reachedBottom) {
              reachedTop = true;
              reachedBottom = false;
            }
          }

          if (ballPosition >= 1.0 && previousPosition < 1.0) {
            if (reachedTop) {
              counter++;
              reachedTop = false;
              reachedBottom = true;

              if (counter == targetCount && !_isPlaying) {
                _playCompletionSound();
              }
            }
          }
        });
      });
    } catch (e) {
      logger.severe('センサー初期化エラー: $e');
      sensorAvailable = false;
    }
  }

  Future<void> _loadTargetCount() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      setState(() {
        targetCount = prefs.getInt('targetCount') ?? 10;
      });
    } catch (e) {
      logger.severe('設定の読み込みエラー: $e');
    }
  }

  Future<void> _saveTargetCount(int value) async {
    try {
      final prefs = await SharedPreferences.getInstance();
      await prefs.setInt('targetCount', value);
    } catch (e) {
      logger.severe('設定の保存エラー: $e');
    }
  }

  Future<void> _playCompletionSound() async {
    try {
      // 成功確認のための安全なコード（エラーを防ぐためにtry-catchを追加）
      // この後でaudioplayers_darwinのSwiftコードが呼び出されます
      await _audioPlayer.play(AssetSource('audio/1.mp3')).catchError((e) {
        // プラットフォームエラーを捕捉して処理
        logger.warning('オーディオプレーヤーエラー: $e');
        return null;
      });
      logger.info('音声の再生を開始しました');
    } catch (e) {
      logger.severe('音楽再生エラー: $e');
      // 静かに失敗、アプリのクラッシュを防ぐ
    }
  }

  Future<void> _stopSound() async {
    await _audioPlayer.stop();
  }

  @override
  void dispose() {
    _audioPlayer.dispose();
    _animationController.dispose();
    _gyroSub?.cancel();
    super.dispose();
  }

  void resetCounter() {
    setState(() {
      counter = 0;
      reachedTop = false;
      reachedBottom = true;
    });
  }

  void increaseSensitivity() {
    setState(() {
      double current = axisSensitivity[selectedAxis] ?? 0.015;
      current += 0.005;
      if (current > 0.2) current = 0.2;
      axisSensitivity[selectedAxis] = current;
    });
  }

  void decreaseSensitivity() {
    setState(() {
      double current = axisSensitivity[selectedAxis] ?? 0.015;
      current -= 0.005;
      if (current < 0.001) current = 0.001;
      axisSensitivity[selectedAxis] = current;
    });
  }

  void toggleInvertAxis() {
    setState(() {
      invertAxis = !invertAxis;
    });
  }

  void changeAxis() {
    setState(() {
      selectedAxis = (selectedAxis + 1) % 3;
    });
  }

  String _getImageBasedOnPosition() {
    if (ballPosition <= 0.2) {
      return 'assets/images/situp_up.png';
    } else if (ballPosition >= 0.8) {
      return 'assets/images/situp_down.png';
    } else {
      return 'assets/images/situp_middle.png';
    }
  }

  void _showGyroscopeSettings() {
    showDialog(
      context: context,
      builder: (BuildContext dialogContext) {
        return StatefulBuilder(
          builder: (context, setDialogState) {
            void onChangeAxis() {
              setState(() {
                selectedAxis = (selectedAxis + 1) % 3;
              });
              setDialogState(() {});
            }

            void onToggleInvertAxis() {
              setState(() {
                invertAxis = !invertAxis;
              });
              setDialogState(() {});
            }

            void onIncreaseSensitivity() {
              setState(() {
                double current = axisSensitivity[selectedAxis] ?? 0.015;
                current += 0.005;
                if (current > 0.2) current = 0.2;
                axisSensitivity[selectedAxis] = current;
              });
              setDialogState(() {});
            }

            void onDecreaseSensitivity() {
              setState(() {
                double current = axisSensitivity[selectedAxis] ?? 0.015;
                current -= 0.005;
                if (current < 0.001) current = 0.001;
                axisSensitivity[selectedAxis] = current;
              });
              setDialogState(() {});
            }

            String sensitivityText =
                (axisSensitivity[selectedAxis] ?? 0.015).toStringAsFixed(3);

            return AlertDialog(
              title: const Text('ジャイロスコープ設定'),
              content: SingleChildScrollView(
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    sensorAvailable
                        ? const Text('センサー: 使用可能',
                            style: TextStyle(color: Colors.green))
                        : const Text('センサー: 使用不可',
                            style: TextStyle(color: Colors.red)),
                    const SizedBox(height: 15),
                    Text('使用軸: ${axisNames[selectedAxis]}',
                        style: const TextStyle(fontWeight: FontWeight.bold)),
                    Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        ElevatedButton(
                          onPressed: onChangeAxis,
                          child: const Text('軸を変更'),
                        ),
                        const SizedBox(width: 10),
                        ElevatedButton(
                          onPressed: onToggleInvertAxis,
                          style: ElevatedButton.styleFrom(
                            backgroundColor: invertAxis ? Colors.orange : null,
                          ),
                          child: Text(invertAxis ? '軸反転: ON' : '軸反転: OFF'),
                        ),
                      ],
                    ),
                    const SizedBox(height: 15),
                    const Text('感度設定',
                        style: TextStyle(fontWeight: FontWeight.bold)),
                    Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Text('${axisNames[selectedAxis]}軸: $sensitivityText'),
                        const SizedBox(width: 10),
                        IconButton(
                          icon: const Icon(Icons.remove),
                          onPressed: onDecreaseSensitivity,
                          tooltip: '感度を下げる',
                        ),
                        IconButton(
                          icon: const Icon(Icons.add),
                          onPressed: onIncreaseSensitivity,
                          tooltip: '感度を上げる',
                        ),
                      ],
                    ),
                    Slider(
                      value: axisSensitivity[selectedAxis] ?? 0.015,
                      min: 0.001,
                      max: 0.2,
                      divisions: 40,
                      label: sensitivityText,
                      onChanged: (value) {
                        setState(() {
                          axisSensitivity[selectedAxis] = value;
                        });
                        setDialogState(() {});
                      },
                    ),
                    const SizedBox(height: 15),
                    StreamBuilder<GyroscopeEvent>(
                      stream: gyroscopeEventStream(),
                      builder: (context, snapshot) {
                        return Container(
                          padding: const EdgeInsets.all(8),
                          decoration: BoxDecoration(
                            border: Border.all(color: Colors.grey),
                            borderRadius: BorderRadius.circular(5),
                          ),
                          child: Column(
                            children: [
                              const Text(
                                'ジャイロセンサーの値',
                                style: TextStyle(fontWeight: FontWeight.bold),
                              ),
                              Text(
                                'X軸: ${gyroX.toStringAsFixed(5)} (感度: ${axisSensitivity[0]?.toStringAsFixed(3)})',
                                style: TextStyle(
                                  color: selectedAxis == 0 ? Colors.red : null,
                                ),
                              ),
                              Text(
                                'Y軸: ${gyroY.toStringAsFixed(5)} (感度: ${axisSensitivity[1]?.toStringAsFixed(3)})',
                                style: TextStyle(
                                  color: selectedAxis == 1 ? Colors.red : null,
                                ),
                              ),
                              Text(
                                'Z軸: ${gyroZ.toStringAsFixed(5)} (感度: ${axisSensitivity[2]?.toStringAsFixed(3)})',
                                style: TextStyle(
                                  color: selectedAxis == 2 ? Colors.red : null,
                                ),
                              ),
                              Text(
                                '現在使用中: ${axisNames[selectedAxis]}軸${invertAxis ? " (反転)" : ""}',
                                style: const TextStyle(
                                    fontWeight: FontWeight.bold),
                              ),
                            ],
                          ),
                        );
                      },
                    ),
                  ],
                ),
              ),
              actions: [
                TextButton(
                  child: const Text('閉じる'),
                  onPressed: () {
                    Navigator.of(context).pop();
                  },
                ),
              ],
            );
          },
        );
      },
    );
  }

  void _showTargetSettingDialog() {
    final TextEditingController controller =
        TextEditingController(text: targetCount.toString());

    showDialog(
      context: context,
      builder: (BuildContext context) {
        return AlertDialog(
          title: const Text('目標回数の設定'),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextField(
                controller: controller,
                keyboardType: TextInputType.number,
                decoration: const InputDecoration(
                  labelText: '目標回数',
                  hintText: '1〜100の間で設定',
                ),
              ),
            ],
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.of(context).pop(),
              child: const Text('キャンセル'),
            ),
            TextButton(
              onPressed: () {
                final newValue = int.tryParse(controller.text);
                if (newValue != null && newValue > 0 && newValue <= 100) {
                  setState(() {
                    targetCount = newValue;
                  });
                  _saveTargetCount(newValue);

                  if (counter >= targetCount && !_isPlaying) {
                    _playCompletionSound();
                  }
                  Navigator.of(context).pop();
                } else {
                  ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(content: Text('1〜100の間で有効な数値を入力してください。')));
                }
              },
              child: const Text('保存'),
            ),
          ],
        );
      },
    );
  }

  void _showScheduleDialog() {
    showDialog(
      context: context,
      builder: (BuildContext context) {
        return AlertDialog(
          title: const Text('トレーニングスケジュール'),
          content: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                ListTile(
                  leading: const Icon(Icons.calendar_today),
                  title: const Text('今日のトレーニング'),
                  subtitle: Text('目標: $targetCount回'),
                ),
                ListTile(
                  leading: const Icon(Icons.fitness_center),
                  title: const Text('現在の進捗'),
                  subtitle: Text('$counter / $targetCount 回 完了'),
                  trailing: CircularProgressIndicator(
                    value: counter / targetCount,
                    backgroundColor: Colors.grey[300],
                    valueColor: AlwaysStoppedAnimation<Color>(
                      counter >= targetCount
                          ? Colors.green
                          : Theme.of(context).primaryColor,
                    ),
                  ),
                ),
                const Divider(),
                const ListTile(
                  leading: Icon(Icons.tips_and_updates),
                  title: Text('トレーニングのヒント'),
                  subtitle: Text('毎日少しずつ増やしていくことが効果的です。'),
                ),
              ],
            ),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.of(context).pop(),
              child: const Text('閉じる'),
            ),
            TextButton(
              onPressed: () {
                Navigator.of(context).pop();
                _showTargetSettingDialog();
              },
              child: const Text('目標を変更'),
            ),
          ],
        );
      },
    );
  }

  Future<void> _checkVibrationSupport() async {
    if (!kIsWeb) {
      try {
        canVibrate = await Vibration.hasVibrator();
      } catch (e) {
        canVibrate = false;
        logger.severe('バイブレーション機能チェックエラー: $e');
      }
    }
  }

  void _vibrateIfNeeded() {
    if (!canVibrate) return;

    final now = DateTime.now();
    if (lastVibration != null &&
        now.difference(lastVibration!).inMilliseconds < 1000) {
      return;
    }

    lastVibration = now;

    try {
      Vibration.vibrate(duration: 500);
      logger.info('バイブレーションを実行');
    } catch (e) {
      logger.severe('バイブレーション実行エラー: $e');
    }
  }

  @override
  Widget build(BuildContext context) {
    String currentImage = _getImageBasedOnPosition();

    bool isDarkMode = widget.themeProvider.themeMode == ThemeMode.dark;

    final colorScheme = Theme.of(context).colorScheme;
    final primaryColor = colorScheme.primary;
    final successColor = colorScheme.tertiary;

    return Scaffold(
      extendBodyBehindAppBar: true,
      appBar: AppBar(
        title: const Text(
          '腹筋トレーニング',
          style: TextStyle(fontWeight: FontWeight.bold),
        ),
        backgroundColor: Colors.transparent,
        elevation: 0,
        actions: [
          IconButton(
            icon: const Icon(Icons.calendar_month),
            onPressed: _showScheduleDialog,
            tooltip: 'スケジュール管理',
          ),
          IconButton(
            icon: const Icon(Icons.edit_note),
            onPressed: _showTargetSettingDialog,
            tooltip: '目標を設定',
          ),
          IconButton(
            icon: const Icon(Icons.settings),
            onPressed: _showGyroscopeSettings,
            tooltip: 'ジャイロスコープ設定',
          ),
          IconButton(
            icon: Icon(isDarkMode ? Icons.light_mode : Icons.dark_mode),
            onPressed: () {
              widget.themeProvider.toggleTheme();
            },
            tooltip: isDarkMode ? 'ライトモードに切替' : 'ダークモードに切替',
          ),
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: resetCounter,
            tooltip: 'リセット',
          ),
        ],
      ),
      body: AnimatedBuilder(
          animation: _backgroundAnimation,
          builder: (context, child) {
            return Container(
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                  colors: isDarkMode
                      ? [
                          Color.lerp(Colors.blueGrey[900], Colors.black,
                              _backgroundAnimation.value)!,
                          Color.lerp(Colors.indigo[900], Colors.blueGrey[800],
                              _backgroundAnimation.value)!,
                        ]
                      : [
                          Color.lerp(Colors.blue[50], Colors.purple[50],
                              _backgroundAnimation.value)!,
                          Color.lerp(Colors.lightBlue[100], Colors.blue[200],
                              _backgroundAnimation.value)!,
                        ],
                ),
              ),
              child: SafeArea(
                child: SingleChildScrollView(
                  physics: const BouncingScrollPhysics(),
                  child: Padding(
                    padding: const EdgeInsets.symmetric(
                        horizontal: 20.0, vertical: 10.0),
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        const SizedBox(height: 20),
                        Card(
                          elevation: 8,
                          color: isDarkMode
                              ? Colors.grey[850]!.withAlpha(179)
                              : Colors.white.withAlpha(230),
                          child: Padding(
                            padding: const EdgeInsets.all(16.0),
                            child: Column(
                              children: [
                                Row(
                                  mainAxisAlignment: MainAxisAlignment.center,
                                  children: [
                                    Text(
                                      'カウンター: $counter',
                                      style: TextStyle(
                                        fontSize: 24,
                                        fontWeight: FontWeight.bold,
                                        color: counter >= targetCount
                                            ? successColor
                                            : null,
                                      ),
                                    ),
                                  ],
                                ),
                                const SizedBox(height: 8),
                                LinearProgressIndicator(
                                  value: targetCount > 0
                                      ? counter / targetCount
                                      : 0,
                                  backgroundColor: isDarkMode
                                      ? Colors.grey[700]
                                      : Colors.grey[300],
                                  valueColor: AlwaysStoppedAnimation<Color>(
                                    counter >= targetCount
                                        ? successColor
                                        : primaryColor,
                                  ),
                                  minHeight: 8,
                                ),
                                const SizedBox(height: 8),
                                GestureDetector(
                                  onTap: _showTargetSettingDialog,
                                  child: Row(
                                    mainAxisAlignment: MainAxisAlignment.center,
                                    children: [
                                      Text(
                                        '目標: $targetCount回',
                                        style: TextStyle(
                                          color: isDarkMode
                                              ? Colors.grey[400]
                                              : Colors.grey[600],
                                        ),
                                      ),
                                      const SizedBox(width: 5),
                                      Icon(
                                        Icons.edit,
                                        size: 16,
                                        color: isDarkMode
                                            ? Colors.grey[400]
                                            : Colors.grey[600],
                                      ),
                                    ],
                                  ),
                                ),
                                if (_isPlaying)
                                  Padding(
                                    padding: const EdgeInsets.only(top: 8.0),
                                    child: ElevatedButton.icon(
                                      icon: const Icon(Icons.stop),
                                      label: const Text('音楽を停止'),
                                      onPressed: _stopSound,
                                      style: ElevatedButton.styleFrom(
                                        backgroundColor: Colors.redAccent,
                                        foregroundColor: Colors.white,
                                      ),
                                    ),
                                  ),
                              ],
                            ),
                          ),
                        ),
                        const SizedBox(height: 30),
                        Card(
                          elevation: 10,
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(20),
                          ),
                          color: isDarkMode
                              ? Colors.grey[850]!.withAlpha(204)
                              : Colors.white.withAlpha(230),
                          child: Padding(
                            padding: const EdgeInsets.all(16.0),
                            child: Column(
                              children: [
                                ClipRRect(
                                  borderRadius: BorderRadius.circular(12),
                                  child: Container(
                                    width: 280,
                                    height: 200,
                                    decoration: BoxDecoration(
                                      border: Border.all(
                                        color: isDarkMode
                                            ? Colors.grey[800]!
                                            : Colors.grey[300]!,
                                        width: 2,
                                      ),
                                      borderRadius: BorderRadius.circular(12),
                                    ),
                                    child: Image.asset(
                                      currentImage,
                                      fit: BoxFit.contain,
                                      width: 240,
                                      height: 180,
                                    ),
                                  ),
                                ),
                                const SizedBox(height: 16),
                                Text(
                                  '下→上→下で1カウント',
                                  style: TextStyle(
                                    fontSize: 18,
                                    fontWeight: FontWeight.w600,
                                    color: isDarkMode
                                        ? Colors.white
                                        : Colors.black87,
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ),
                        const SizedBox(height: 30),
                        Card(
                          elevation: 5,
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(16),
                          ),
                          color: isDarkMode
                              ? Colors.grey[900]!.withAlpha(153)
                              : Colors.white.withAlpha(204),
                          child: Padding(
                            padding: const EdgeInsets.all(16.0),
                            child: Column(
                              children: [
                                const Icon(Icons.info_outline, size: 28),
                                const SizedBox(height: 8),
                                kIsWeb
                                    ? const Text(
                                        '※Webブラウザではセンサーとバイブレーションが使えない場合があります',
                                        style: TextStyle(color: Colors.red),
                                        textAlign: TextAlign.center,
                                      )
                                    : Column(
                                        children: [
                                          const Text('端末を前後に傾けて腹筋運動をしてください',
                                              textAlign: TextAlign.center),
                                          const SizedBox(height: 8),
                                          Text(
                                            canVibrate
                                                ? '最上部でバイブレーションします'
                                                : 'バイブレーション機能は使用できません',
                                            style: TextStyle(
                                              fontWeight: FontWeight.bold,
                                              color: canVibrate
                                                  ? successColor
                                                  : Colors.orange,
                                            ),
                                            textAlign: TextAlign.center,
                                          ),
                                        ],
                                      ),
                              ],
                            ),
                          ),
                        ),
                        const SizedBox(height: 20),
                      ],
                    ),
                  ),
                ),
              ),
            );
          }),
    );
  }
}
