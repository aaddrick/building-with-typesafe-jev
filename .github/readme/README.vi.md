<p align="center">
  <img src="../assets/hero.png" alt="Building with TypeSafe Jev: quyết định có kiểu với độ tin cậy đã hiệu chỉnh, dành cho tác nhân lập trình của bạn. Tham khảo từ hơn 150 dự án cộng đồng, xếp theo dạng. Hai khung. Bên trái, một LLM dùng Structured Outputs trả về JSON hợp lệ: department: billing, severity: medium, refund: false (tô đỏ), và độ tin cậy 0.95, nhưng độ tin cậy này do mô hình tự sinh ra, không được hiệu chỉnh. Bên phải, một lệnh gọi Jev trả về ba câu trả lời có kiểu: một Choice (department: billing, độ tin cậy 0.88), một Score (severity: 1.43 trên 2), và một Noul (refund: 0.99)." width="100%">
</p>

<p align="center">
  <strong>Building with TypeSafe Jev</strong><br>
  <em>Quyết định có kiểu với độ tin cậy đã hiệu chỉnh, dành cho tác nhân lập trình của bạn.</em><br>
  <em>Tham khảo từ hơn 150 dự án cộng đồng, xếp theo dạng.</em>
</p>

<p align="center">
  <a href="../../LICENSE"><img src="https://img.shields.io/github/license/aaddrick/building-with-typesafe-jev?style=flat" alt="License"></a>
  <a href="../workflows/checks.yml"><img src="https://img.shields.io/github/actions/workflow/status/aaddrick/building-with-typesafe-jev/checks.yml?label=checks&style=flat" alt="Checks"></a>
</p>

<p align="center">
  <a href="https://www.linkedin.com/in/aaddrick/">Kết nối trên LinkedIn!</a>
</p>

<p align="center">
  <a href="../../README.md">English</a> ·
  <a href="README.zh-CN.md">简体中文</a> ·
  <a href="README.ja.md">日本語</a> ·
  <a href="README.ko.md">한국어</a> ·
  <strong>Tiếng Việt</strong> ·
  <a href="README.pt-BR.md">Português (BR)</a> ·
  <a href="README.it.md">Italiano</a> ·
  <a href="README.en-x-aibro.md">AI Bro</a>
</p>

> [!NOTE]
> Đây là một skill không chính thức do cộng đồng làm. TypeSafe AI không làm, không duyệt và không bảo trợ nó. TypeSafe có skill riêng tại [typesafe-ai/skills](https://github.com/typesafe-ai/skills). Xem [Khác biệt so với skill chính thức](#khác-biệt-so-với-skill-chính-thức).

Các tác nhân lập trình đối xử với Jev như thêm một chat model nữa. Skill này dạy chúng thiết kế cho nó: câu hỏi có kiểu, độ tin cậy đã hiệu chỉnh, và một thư viện hơn 150 dự án cộng đồng xếp theo cách chúng hoạt động. Nó cài được trong Claude Code, Codex và Antigravity CLI.

## Cài đặt

<details>
<summary><strong>Claude Code</strong></summary>

Chạy hai lệnh này trong terminal:

```bash
claude plugin marketplace add aaddrick/building-with-typesafe-jev
```

```bash
claude plugin install building-with-typesafe-jev@building-with-typesafe-jev
```

Skill tự tải khi bạn làm việc với code Jev. Muốn tải thủ công, hãy gõ:

```
/building-with-typesafe-jev:building-with-typesafe-jev
```

Quá trình cài đặt có thể báo rằng một tùy chọn của plugin chưa được đặt. Đó là kiểm thử trực tiếp, vẫn tắt cho tới khi bạn bật nó. Xem [Thiết lập API key](#thiết-lập-api-key-không-bắt-buộc-nên-có).

</details>

<details>
<summary><strong>Codex</strong></summary>

```bash
codex plugin marketplace add aaddrick/building-with-typesafe-jev
```

```bash
codex plugin add building-with-typesafe-jev@building-with-typesafe-jev
```

Mở một thread mới. Codex tải skill khi tác vụ phù hợp. Muốn tải thủ công, hãy gõ:

```
$building-with-typesafe-jev:building-with-typesafe-jev
```

</details>

<details>
<summary><strong>Antigravity CLI</strong></summary>

```bash
agy plugin install https://github.com/aaddrick/building-with-typesafe-jev
```

Kiểm tra xem nó đã được cài chưa:

```bash
agy plugin list
```

Bắt đầu một phiên mới. Antigravity CLI tải skill khi tác vụ phù hợp. Muốn tải thủ công, hãy gõ:

```
/building-with-typesafe-jev:building-with-typesafe-jev
```

Chuyển từ Gemini CLI sang? Nếu `agy plugin import gemini` đã mang extension này qua, bạn vẫn nên chạy lệnh cài đặt ở trên. Lệnh này thay thế bản đã import, vì lệnh thiết lập của bản đó không chạy được trong Antigravity CLI.

</details>

<details>
<summary><strong>Tác nhân khác có đọc SKILL.md</strong></summary>

Sao chép thư mục `skills/building-with-typesafe-jev/` vào thư mục skill của tác nhân. Giữ nguyên cả thư mục. `SKILL.md` liên kết tới các file nằm cạnh nó.

</details>

## Thiết lập API key (không bắt buộc, nên có)

Skill vẫn hoạt động khi không có key. Nó vẫn chọn primitive, viết câu hỏi và code, rồi đối chiếu chúng với tài liệu tham chiếu API của nó. Khi có key, nó còn kiểm thử từng thiết kế bằng lệnh gọi API thật trước khi code tới dự án của bạn. Cách này bắt được tên trường sai và những câu hỏi mà Jev hiểu khác với ý bạn. Mỗi lệnh gọi tốn chưa tới một xu, nên chúng tôi rất khuyến khích dùng key.

Kiểm thử trực tiếp tắt cho tới khi bạn bật nó. Khi nó tắt, skill không bao giờ tìm key. Khi nó bật, skill chỉ đọc key từ biến môi trường bạn chỉ định (`TYPESAFE_API_KEY` nếu bạn không chọn biến khác), báo cho bạn trước lệnh gọi đầu tiên, và giữ ở mức khoảng 10 lệnh gọi thử cho mỗi tác vụ. Ba bước: tạo key, lưu trữ key, và bật kiểm thử trực tiếp.

<details>
<summary><strong>Tạo key</strong> (bốn bước trong console TypeSafe)</summary>

**Bước 1.** Đăng nhập tại [console.typesafe.ai](https://console.typesafe.ai/) và mở **API Keys** ở thanh bên.

<img src="../assets/api-key/step-1.png" alt="Trang chủ console TypeSafe. Một khung và mũi tên màu hổ phách chỉ vào API Keys ở thanh bên trái." width="100%">

**Bước 2.** Nhấn **Create key** (tạo key) ở góc trên bên phải.

<img src="../assets/api-key/step-2.png" alt="Trang API keys. Các key hiện có bị làm mờ. Một khung và mũi tên màu hổ phách chỉ vào nút Create key ở góc trên bên phải." width="100%">

**Bước 3.** Đặt tên key theo nơi nó sẽ được dùng, chẳng hạn tên máy hoặc tên tác nhân. Sau đó nhấn **Create key**.

<img src="../assets/api-key/step-3.png" alt="Hộp thoại Create API key với tên my-coding-agent đã được nhập. Một khung và mũi tên màu hổ phách chỉ vào ô tên và nút Create key." width="100%">

**Bước 4.** Sao chép key ngay bây giờ. Console chỉ hiển thị nó một lần. Nếu làm mất, hãy tạo key mới và thu hồi key cũ.

<img src="../assets/api-key/step-4.png" alt="Hộp thoại API key created. Giá trị key bị che. Một khung và mũi tên màu hổ phách chỉ vào nút Copy." width="100%">

</details>

<details>
<summary><strong>Lưu trữ key</strong> (macOS, Linux, Windows)</summary>

Giữ key trong một file riêng mà chỉ bạn đọc được. Skill đọc key từ một biến môi trường, không bao giờ từ file, nên biến đó phải được đặt trong các shell mà tác nhân của bạn khởi động. Tác nhân thường khởi động shell mà không có terminal, nên mỗi phần dưới đây đặt key ở nơi các shell đó nhìn thấy được. Chọn hệ thống của bạn.

<details>
<summary><strong>macOS</strong> (zsh, shell mặc định)</summary>

Lưu key vào một file riêng:

```bash
mkdir -p ~/.config/typesafe && umask 077 && printf 'export TYPESAFE_API_KEY=%s\n' 'YOUR_KEY' > ~/.config/typesafe/env
```

Nạp nó từ `~/.zshenv`. Mọi zsh đều đọc file này, kể cả các shell mà tác nhân khởi động không có terminal. `~/.zshrc` chỉ được đọc bởi shell tương tác.

```bash
echo '[ -f ~/.config/typesafe/env ] && . ~/.config/typesafe/env' >> ~/.zshenv
```

Mở một terminal mới và kiểm tra. Lệnh này in ra độ dài của key, không in key:

```bash
echo ${#TYPESAFE_API_KEY}
```

</details>

<details>
<summary><strong>Linux với bash</strong> (Ubuntu, Debian, Mint, Fedora, Arch)</summary>

Lưu key vào một file riêng:

```bash
mkdir -p ~/.config/typesafe && umask 077 && printf 'export TYPESAFE_API_KEY=%s\n' 'YOUR_KEY' > ~/.config/typesafe/env
```

Nạp nó ở **đầu** `~/.bashrc`. Ubuntu, Debian, Mint và Arch mở đầu `~/.bashrc` bằng một dòng dừng sớm khi không có terminal. Một dòng nằm dưới điều kiện đó sẽ không bao giờ chạy với shell của tác nhân. Đầu file thì an toàn trên mọi bản phân phối:

```bash
sed -i '1i [ -f ~/.config/typesafe/env ] \&\& . ~/.config/typesafe/env' ~/.bashrc
```

Mở một terminal mới và kiểm tra:

```bash
echo ${#TYPESAFE_API_KEY}
```

</details>

<details>
<summary><strong>Linux với zsh</strong></summary>

Làm theo các bước cho macOS. zsh đọc `~/.zshenv` theo cùng cách trên Linux.

</details>

<details>
<summary><strong>Linux với fish</strong></summary>

fish đọc mọi file trong `~/.config/fish/conf.d/`, dù có terminal hay không:

```fish
mkdir -p ~/.config/fish/conf.d; and echo 'set -gx TYPESAFE_API_KEY YOUR_KEY' > ~/.config/fish/conf.d/typesafe.fish; and chmod 600 ~/.config/fish/conf.d/typesafe.fish
```

```fish
string length -- $TYPESAFE_API_KEY
```

</details>

<details>
<summary><strong>Windows</strong> (PowerShell)</summary>

Lưu key dưới dạng biến môi trường người dùng. Terminal và ứng dụng mới sẽ thấy nó. Terminal đang mở thì không:

```powershell
[Environment]::SetEnvironmentVariable('TYPESAFE_API_KEY', 'YOUR_KEY', 'User')
```

Mở một terminal mới và kiểm tra:

```powershell
$env:TYPESAFE_API_KEY.Length
```

**WSL:** Theo mặc định, biến của Windows không truyền vào WSL. Bên trong WSL, hãy làm theo các bước cho Linux với bash.

</details>

<details>
<summary><strong>Ứng dụng desktop và tiện ích mở rộng IDE</strong></summary>

Ứng dụng bạn khởi động từ dock, start menu hay trình khởi chạy desktop không đọc các file shell của bạn.

- **Windows:** biến môi trường người dùng ở trên đã bao gồm các ứng dụng này.
- **Linux (systemd):** thêm dòng `TYPESAFE_API_KEY=YOUR_KEY` vào `~/.config/environment.d/typesafe.conf`, rồi đăng xuất và đăng nhập lại.
- **macOS:** khởi động ứng dụng từ terminal, hoặc đặt biến trong phần cài đặt riêng của ứng dụng. macOS không có file đơn giản theo từng người dùng mà ứng dụng desktop đọc.

</details>

</details>

<details>
<summary><strong>Bật kiểm thử trực tiếp</strong> (Claude Code, Codex, Antigravity CLI)</summary>

Mỗi tác nhân giữ hai thiết lập: kiểm thử trực tiếp (`on` hoặc `off`, mặc định `off`) và tên của biến chứa key (mặc định `TYPESAFE_API_KEY`). Đặt chúng một lần. Chúng có hiệu lực từ phiên tiếp theo. Các script hỗ trợ cần Python 3; script cho Codex cần 3.11 trở lên.

**Claude Code.** Chạy lệnh này trong terminal:

```bash
claude plugin install building-with-typesafe-jev@building-with-typesafe-jev --config live_testing=on
```

Nếu key của bạn nằm trong một biến có tên khác, hãy thêm `--config key_env_var=YOUR_VARIABLE`. Trong một phiên, `/plugin configure building-with-typesafe-jev@building-with-typesafe-jev` thay đổi cùng các thiết lập đó.

**Codex.** Codex không có thiết lập plugin, nên skill giữ chúng trong `~/.codex/config.toml`, file mà Codex truyền cho mọi shell tác nhân khởi động. Trong một phiên, hãy gõ:

```
$building-with-typesafe-jev:jev-settings live on
```

Codex sẽ hỏi để phê duyệt việc ghi file. Muốn thay đổi thủ công, hãy thêm các dòng này vào `~/.codex/config.toml`:

```toml
[shell_environment_policy.set]
JEV_LIVE_TESTING = "on"
JEV_KEY_ENV_VAR = "TYPESAFE_API_KEY"
```

Codex cũng yêu cầu bạn tin cậy hook khởi động phiên của plugin một lần. Vào đầu mỗi phiên, hook cho tác nhân biết kiểm thử trực tiếp có đang bật không và biến chứa key đã được đặt chưa, không bao giờ cho biết chính key. Trong một phiên, gõ `/hooks` rồi tin cậy hook đó. Codex sẽ hỏi lại khi một bản cập nhật thay đổi hook. Cho đến khi bạn tin cậy, hook không chạy, và skill vẫn tự kiểm tra các thiết lập.

**Antigravity CLI.** Antigravity CLI không có thiết lập cho plugin, nhưng shell của tác nhân kế thừa môi trường của terminal đã khởi động `agy`. Vì vậy hai thiết lập chính là hai biến môi trường, đặt ở nơi bạn lưu key. Nếu key nằm trong `~/.config/typesafe/env`, hãy chạy lệnh này, rồi mở terminal mới và khởi động lại `agy`:

```bash
echo 'export JEV_LIVE_TESTING=on' >> ~/.config/typesafe/env
```

Nếu key nằm trong một biến có tên khác, hãy thêm `export JEV_KEY_ENV_VAR=YOUR_VARIABLE` theo cách tương tự. Trên fish hoặc Windows, hãy đặt `JEV_LIVE_TESTING` thành `on` theo cách bạn đã lưu key.

**Kiểm tra.** Bắt đầu một phiên mới và chạy lệnh thiết lập: `/building-with-typesafe-jev:jev-settings` trong Claude Code, `$building-with-typesafe-jev:jev-settings` trong Codex, hoặc `/building-with-typesafe-jev:jev-settings` trong Antigravity CLI. Lệnh này hiển thị cả hai thiết lập và cho biết shell của tác nhân có thấy key hay không. Nó in ra độ dài của key, không bao giờ in key.

**CI và container.** Các biến môi trường `JEV_LIVE_TESTING` và `JEV_KEY_ENV_VAR` ghi đè các thiết lập đã lưu trong mọi tác nhân.

</details>

<details>
<summary><strong>Nếu tác nhân không thấy key</strong></summary>

Lệnh thiết lập báo `key: not set in this shell` khi shell của tác nhân không có biến đó. Hãy kiểm tra lần lượt:

- **Bạn khởi động tác nhân trước khi lưu key.** Shell của tác nhân sao chép môi trường của chương trình đã khởi động chúng. Thoát tác nhân và khởi động lại từ một terminal mới.
- **Bạn khởi động tác nhân từ dock, start menu hoặc một IDE.** Các ứng dụng đó không đọc các file shell của bạn. Xem "Ứng dụng desktop và tiện ích mở rộng IDE" ở trên.
- **Codex lọc môi trường.** Nếu `~/.codex/config.toml` đặt `include_only` trong `[shell_environment_policy]`, hãy thêm biến chứa key, `JEV_LIVE_TESTING` và `JEV_KEY_ENV_VAR` vào đó. Nếu nó đặt `ignore_default_excludes = false`, Codex bỏ mọi biến có `KEY` trong tên. Hãy xóa dòng đó.
- **WSL.** Biến của Windows không truyền vào WSL. Hãy lưu key bên trong WSL theo các bước cho Linux.

</details>

Skill không bao giờ in, ghi log hay hardcode key. Nó chỉ đọc biến bạn chỉ định, và truyền key cho từng lệnh kiểm thử mà không đặt key lên dòng lệnh.

## Nó làm gì

Một LLM có thể trả về JSON, và với Structured Outputs thì JSON lần nào cũng parse được. Nhưng nó vẫn có thể sai, và không có gì trong đầu ra cho bạn biết nó sai thường xuyên tới mức nào. Schema cố định hình dạng của câu trả lời, không cố định bản thân câu trả lời. Trường department vẫn ghi "billing" dù model biết hay chỉ đoán. Nếu bạn thêm một trường độ tin cậy, model viết con số đó theo đúng cách nó viết câu trả lời. Con số ấy không được hiệu chỉnh theo bất cứ thứ gì.

[Jev](https://docs.typesafe.ai/introduction) là một model [System One](https://docs.typesafe.ai/concepts/system-one) của TypeSafe AI. Nó không viết văn bản. Xác suất của nó được tối ưu theo kết quả thực tế, không phải lấy mẫu từ bộ giải mã, và phần lớn truy vấn trả về trong 100 tới 200 ms. Bạn gửi cho nó một nội dung, chẳng hạn một ticket hỗ trợ, cùng một bộ câu hỏi. Nó trả lời mỗi câu hỏi bằng một giá trị có kiểu kèm xác suất đã hiệu chỉnh. Không có văn bản nào cần parse. Một câu hỏi thuộc một trong ba kiểu:

- **Choice** chọn một lựa chọn từ danh sách bạn đưa ra. Ví dụ: bước tiếp theo của một tác nhân, chọn giữa tìm trong tài liệu, chạy test, hoặc hỏi người dùng. Đó là định tuyến công cụ mà không có LLM nào trong vòng lặp.
- **Score** đặt nội dung lên một thang đo mà bạn mô tả từng bậc. Ví dụ: chấm pull request của một tác nhân trên thang bỏ qua spec → đáp ứng một phần spec → đáp ứng spec. Nó rơi vào mức 1.6, đã gần tới mức đáp ứng spec.
- **Noul** cho biết xác suất một mệnh đề có/không là đúng. Ví dụ: "lệnh shell này xóa file nằm ngoài dự án" trả về 0.97, và một cổng phê duyệt chặn lệnh đó trước khi nó chạy.

Đọc tài liệu tham chiếu API là phần dễ. Phần khó là thiết kế cho một model không viết văn bản. Một tác nhân không có skill này sẽ tìm một bài hướng dẫn, đoán phần còn lại của API, và mang thói quen viết prompt rồi parse sang một model được tạo ra để thay thế chính những thói quen đó. Skill này đưa cho tác nhân API, các quy tắc thiết kế, các lỗi đã biết, và bản đồ những gì người khác đã làm. Tài liệu mô tả model. Skill chỉ cách thiết kế cho nó.

## Điều gì thay đổi

Chúng tôi giao cho một tác nhân lập trình sáu tác vụ Jev, chẳng hạn một hàm phân loại ticket hỗ trợ và một cổng phê duyệt cho lệnh shell. Tác nhân có tài liệu nhưng không có API key, nên người chấm kiểm tra code nó viết, không phải những gì code đó làm khi chạy với Jev. Mỗi tác vụ chạy 10 lần trong mỗi thiết lập trong ba thiết lập, tất cả được khởi chạy cùng lúc trong một đợt eval.

| | Không có skill | Skill này | Skill chính thức |
|---|---:|---:|---:|
| Điểm trung bình | 0.65 | 0.96 | 0.77 |

Điểm là tỷ lệ tiêu chí mà một lần chạy đạt. Mỗi điểm trung bình chính xác trong phạm vi 0.05, với độ tin cậy 95%.

### Nơi skill này tạo ra khác biệt

Đây là các tiêu chí mà khoảng cách giữa skill này và khi không có skill quá lớn để là ngẫu nhiên, theo một kiểm định 95% trên số lần đạt. Mỗi số là số lần chạy đạt trên 10.

| Code của tác nhân... | Không có skill | Skill này | Skill chính thức |
|---|---:|---:|---:|
| đếm trong code, thay vì hỏi Jev một con số | 1 | 8 | 0 |
| nêu tên một trường của đầu vào trong các câu hỏi | 0 | 10 | 1 |
| cố định hoặc ghi lại phiên bản model Jev | 0 | 10 | 0 |
| giữ nhiều hơn một đường đi khi duyệt qua 1,200 danh mục | 1 | 10 | 7 |
| cho danh sách phòng ban một lựa chọn dành cho mọi trường hợp còn lại | 3 | 10 | 6 |
| hỏi cổng lệnh nhiều hơn một câu có/không | 5 | 10 | 9 |
| hỏi một câu cho mỗi mục của rubric và tính điểm trong code | 5 | 10 | 10 |

Một phép khớp mẫu chấm ba tiêu chí trong số này. Bốn tiêu chí còn lại do ba người chấm LLM từ ba nhà cung cấp chấm, Claude Opus, GPT-6 Sol và Kimi K3, và đa số quyết định. Tác nhân là một mô hình Claude, nên một người chấm Claude không bao giờ tự mình quyết định.

### So với skill chính thức

Theo cùng kiểm định đó, skill này đạt thường xuyên hơn skill chính thức ở tám tiêu chí. Bốn tiêu chí nằm trong bảng: phép đếm, tên trường, phiên bản model, và lựa chọn còn lại. Bốn tiêu chí kia:

- giữ một quy tắc bằng code thuần chặn một lệnh phá hủy, hoặc chuyển nó cho một người, bất kể Jev nói gì: 10 lần chạy so với 2
- đọc xác suất mức nghiêm trọng theo khóa số nguyên: 10 so với 4
- hiểu `score` là vị trí từ 0 tới n-1: 10 so với 5
- giữ trình gán nhãn log ở mức tối đa 8 yêu cầu cùng lúc: 10 so với 6

### Nơi nó không tạo ra khác biệt

- Một tiêu chí làm các người chấm bất đồng, nên nó không có trong bảng. Với Opus và GPT-6 Sol, skill này không để lý do của chính tác nhân phê duyệt một lệnh ở 10 lần chạy, so với 5 khi không có skill. Kimi K3 cho đạt 9 trên 10 lần chạy không có skill đó.
- Định tuyến theo `confidence` đạt 2 trên 10 lần chạy với skill này và 2 trên 10 khi không có skill. Tác vụ chưa bao giờ nói ticket không chắc chắn nên đi đâu, nên phần lớn tác nhân trả về giá trị độ tin cậy và để bên gọi tự quyết định. Chính skill cũng nói như vậy là ổn khi code chỉ chọn phương án tốt nhất. Giờ tác vụ đã chỉ rõ một phương án dự phòng, và đợt eval tiếp theo sẽ kiểm tra điều đó.
- Mọi tiêu chí khác hoặc đạt ở gần như mọi lần chạy trong cả ba thiết lập, hoặc chênh lệch ít hơn mức ngẫu nhiên.

[evals README](../../evals/README.md) có mọi tiêu chí kèm khoảng của nó, và cách chạy bộ eval.

## Bên trong có gì

Skill tải theo từng lớp, nên tác nhân chỉ đọc những gì tác vụ cần. Một file lớn duy nhất sẽ khiến tác nhân tốn token và sự chú ý ở mọi tác vụ, trước khi nó viết dòng code nào.

| File | Nội dung | Khi nào tác nhân đọc |
|---|---|---|
| `SKILL.md` | Chọn primitive nào, 11 quy tắc thiết kế, cách dùng xác suất và độ tin cậy, phải làm gì khi một câu trả lời sai, các lỗi thường gặp | Mọi tác vụ Jev |
| `api-reference.md` | HTTP API, SDK Python và JavaScript, giới hạn, lỗi, biến môi trường | Khi viết code |
| `patterns.md` | 4 pattern chính thức và các kỹ thuật từ 18 cookbook, kèm ngưỡng của chúng | Khi thiết kế một workflow |
| `prior-art/INDEX.md` | Bản đồ từ "thứ tôi muốn làm" tới một dạng, cùng các ý tưởng đã thất bại | Trước khi thiết kế thứ gì mới |
| `prior-art/*.md` | 11 file dạng: một đoạn code mẫu, bài học thực tế, và các dự án liên kết | Một hoặc hai file cho mỗi thiết kế |
| `scripts/jev_live.py` | Đọc các thiết lập kiểm thử trực tiếp, và chạy một lệnh kiểm thử với key | Trước một lệnh gọi kiểm thử trực tiếp |
| `../jev-settings/` | Lệnh thiết lập cho Claude Code, Codex và Antigravity CLI | Khi bạn chạy nó |

## Thư viện tham khảo

Hầu hết các danh mục xếp dự án theo ngành. Thư viện này xếp chúng theo dạng triển khai. Một bot chơi game, một drone và một bot giao dịch có chung một dạng: vòng điều khiển. Xếp theo cách đó, cả ba dùng chung một đoạn code mẫu và một bộ bài học thực tế. 11 dạng:

- **Vòng điều khiển**: game, drone, robot, thị trường.
- **Chọn từ các ứng viên**: tác nhân trình duyệt và điện thoại, gọi công cụ không cần LLM, trích xuất, bộ định tuyến.
- **Cổng kiểm soát**: duyệt lệnh gọi công cụ, kiểm tra "đã xong", CI, tiền, nội dung.
- **Bộ lọc luồng**: lọc nội dung rác, kiểm duyệt, email, log, gán nhãn hàng loạt.
- **Xếp hạng và so khớp**: reranker, so khớp thực thể, duyệt đồ thị và phân loại.
- **Giám khảo và đánh giá**: giám khảo theo rubric, chấm trace, review code để phân loại.
- **Tăng dần và thời gian thực**: lồng tiếng, giọng nói, giao diện chạy theo phím gõ.
- **Ngữ cảnh và bộ nhớ của tác nhân**: nén ngữ cảnh, cổng bộ nhớ, hết hạn bộ nhớ, điều chỉnh mức nỗ lực.
- **Kết hợp với LLM**: planner và actor, kiểm tra rồi mới chuyển lên, chưng cất (distillation).
- **Câu trả lời là dữ liệu**: đặc trưng cho model cổ điển, công cụ nghiên cứu, benchmark.
- **Nhúng vào hạ tầng**: hàm SQL, cơ sở dữ liệu vector, hook CI, Home Assistant.

Chỉ mục cũng liệt kê các ý tưởng đã thất bại trong thực tế: cờ vua, review code khi Jev là người review duy nhất, nhận thức hình ảnh, và tin vào hiệu chỉnh mà không kiểm tra. Một lần thử thất bại giúp người làm sau khỏi lặp lại nó.

## Cách kiểm thử

Chúng tôi kiểm thử skill theo cách bạn kiểm thử code: xem nó thất bại trước, rồi sửa.

1. Chúng tôi chạy một tác vụ phân loại không có skill và ghi lại mọi phỏng đoán và mọi lỗi.
2. Chúng tôi viết skill để sửa những lỗi đó.
3. Một tác nhân mới chạy lại cùng tác vụ với skill, rồi liệt kê những chỗ chưa rõ. Chúng tôi sửa sáu chỗ thiếu.
4. Chúng tôi đối chiếu các sự thật về API trong skill với API thật, dùng Python SDK 0.7.1 và model `jev-1.13.0`.
5. Chúng tôi chạy ba đoạn code mẫu trong thư viện tham khảo với API thật. Một lần chạy cho thấy Jev hiểu câu hỏi kiểm tra ảo giác theo nghĩa đen, và bài học đó giờ đã có trong skill.
6. Một tác nhân mới thử ba thiết kế mới chỉ với chỉ mục. Nó tìm đúng dạng cho từng thiết kế và báo hai chỗ thiếu. Chúng tôi sửa cả hai.
7. Chúng tôi cài plugin trong Claude Code, Codex và Antigravity CLI, và kiểm tra rằng mỗi công cụ đều tải được skill.
8. Chúng tôi chạy sáu trường hợp eval, mỗi trường hợp mười lần với skill này, không có skill, và với skill chính thức, mỗi nhóm trong một container cô lập riêng. Xem [Điều gì thay đổi](#điều-gì-thay-đổi) và [evals README](../../evals/README.md).

## Cập nhật

Jev thay đổi nhanh. Skill là bản chụp của [docs.typesafe.ai](https://docs.typesafe.ai/llms.txt) và của cộng đồng vào ngày 2026-09-25. Nó bảo tác nhân rằng tài liệu trực tuyến luôn đúng hơn khi có mâu thuẫn, và chỉ cách tải tài liệu đó dưới dạng Markdown. Khi một sự thật trong skill bị sai, hãy mở issue kèm liên kết tới nguồn.

## Khác biệt so với skill chính thức

[Skill chính thức của TypeSafe](https://github.com/typesafe-ai/skills) ngắn gọn và trỏ tác nhân tới tài liệu trực tuyến. Đó là nguồn đúng cho chi tiết API hiện tại. Bạn có thể cài cả nó nếu muốn.

Skill này chứa nhiều hơn ngay bên trong: hình dạng chính xác của API, các ngưỡng từ cookbook, các lỗi mà cộng đồng gặp phải, và thư viện tham khảo. Tác nhân có thể thiết kế mà không cần gọi mạng, và có thể tìm những gì người khác đã làm trước khi bắt đầu.

Trên sáu tác vụ eval, skill chính thức đạt 0.77 ± 0.04, so với 0.65 ± 0.05 khi không có skill và 0.96 ± 0.02 với skill này. Xem [evals README](../../evals/README.md).

## Ghi công

Các sự thật về API lấy từ tài liệu công khai và cookbook của TypeSafe AI. Phần tham khảo đến từ những người đã công bố dự án của mình, từ cộng đồng Hacker News, và từ các chỉ mục sau: [awesome-jev-typesafe](https://github.com/valentynkit/awesome-jev-typesafe), [JevDirectory](https://www.jevdirectory.org/resources), [awesome-jev-use-cases](https://github.com/walidboulanouar/awesome-jev-use-cases), và [awesome-typesafe-jev](https://github.com/AbdelStark/awesome-typesafe-jev). Mỗi file dạng đều liên kết tới các dự án gốc.

TypeSafe, Jev và System One là tên của TypeSafe AI. Dự án này chỉ dùng chúng để nói skill dùng cho việc gì.

## Giấy phép

MIT. Xem [LICENSE](../../LICENSE).
