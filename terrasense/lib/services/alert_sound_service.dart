import 'package:flutter/material.dart';
import 'package:just_audio/just_audio.dart';
import 'package:wakelock_plus/wakelock_plus.dart';
import '../screens/alert_screen.dart';

class AlertSoundService {
  static AudioPlayer? _player;
  static final GlobalKey<NavigatorState> navigatorKey =
      GlobalKey<NavigatorState>();

  static Future<void> playAlert(String message, double distanceKm) async {
    try {
      await WakelockPlus.enable();

      _player ??= AudioPlayer();

      // Standard asset loading method for just_audio
      await _player!.setAsset('assets/sounds/alert.mp3');
      await _player!.setVolume(1.0);
      await _player!.setLoopMode(LoopMode.one);
      await _player!.play();

      WidgetsBinding.instance.addPostFrameCallback((_) {
        navigatorKey.currentState?.push(
          MaterialPageRoute(
            builder: (_) => AlertScreen(
              message: message,
              distanceKm: distanceKm,
            ),
          ),
        );
      });

      print('[AlertSoundService] 🔊 Playing alert audio.');
    } catch (e) {
      print('[AlertSoundService] Sound error: $e');
    }
  }

  static Future<void> stopAlert() async {
    await _player?.stop();
    await _player?.dispose();
    _player = null;
    await WakelockPlus.disable();
  }
}