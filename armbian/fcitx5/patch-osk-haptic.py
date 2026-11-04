"""Keep the F8 keyboard's accepted 30ms feedback in the Fcitx5 OSK."""
from pathlib import Path
import sys
src=Path(sys.argv[1]);p=src/'fcitx5-osk/src/state/keyboard.rs'
s=p.read_text()
if 'async fn f8_key_haptic()' not in s:
 s=s.replace('const TEXT_PADDING_LENGTH: u32 = 3;', '''const TEXT_PADDING_LENGTH: u32 = 3;

// F8: feedback failures never block text input. No root helper per keystroke.
async fn f8_key_haptic() {
    if std::env::var("F8_OSK_HAPTICS").as_deref() == Ok("0") { return; }
    static BUS: std::sync::OnceLock<Connection> = std::sync::OnceLock::new();
    let action = async {
        if BUS.get().is_none() {
            if let Ok(c) = Connection::session().await { let _ = BUS.set(c); }
        }
        if let Some(c) = BUS.get() {
            let _: zbus::Result<bool> = c.call_method(
                Some("org.sigxcpu.Feedback"), "/org/sigxcpu/Feedback",
                Some("org.sigxcpu.Feedback.Haptic"), "Vibrate",
                &("org.kde.plasma.keyboard", vec![(1.0_f64, 30_u32)]),
            ).await.and_then(|reply| reply.body().deserialize());
        }
    };
    let _ = tokio::time::timeout(Duration::from_millis(150), action).await;
}''')
 old='''                return self
                    .clear_custom_action()
                    .chain(self.press_key(common, key_widget_event));'''
 new='''                let typing = self.clear_custom_action()
                    .chain(self.press_key(common, key_widget_event));
                return Task::batch([typing, Task::perform(f8_key_haptic(), |_| Message::Nothing)]);'''
 assert s.count(old)==1
 s=s.replace(old,new);p.write_text(s)
