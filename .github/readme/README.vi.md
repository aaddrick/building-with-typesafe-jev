<p align="center">
  <strong>Building with TypeSafe Jev</strong><br>
  <em>Quyết định có kiểu với độ tin cậy đã hiệu chỉnh, dành cho tác nhân lập trình của bạn.</em><br>
  <em>Liên kết tới hơn 150 dự án cộng đồng, xếp theo dạng, mỗi dạng có một bản phác thảo code.</em>
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
  <a href="README.it.md">Italiano</a>
</p>

> [!NOTE]
> Đây là một skill không chính thức do cộng đồng làm. TypeSafe AI không làm, không duyệt và không bảo trợ nó. TypeSafe có skill riêng tại [typesafe-ai/skills](https://github.com/typesafe-ai/skills). Xem [Khác biệt so với skill chính thức](#khác-biệt-so-với-skill-chính-thức).

Các tác nhân lập trình đối xử với Jev như thêm một chat model nữa. Skill này dạy chúng thiết kế cho nó: câu hỏi có kiểu, độ tin cậy đã hiệu chỉnh, và liên kết tới hơn 150 dự án cộng đồng, xếp theo cách chúng hoạt động, mỗi mẫu có một bản phác thảo code. Nó cài được trong Claude Code, Codex và Antigravity CLI.

[Jev](https://docs.typesafe.ai/introduction) là một model [System One](https://docs.typesafe.ai/concepts/system-one). Nó không viết văn bản. Bạn gửi cho nó một nội dung cùng một bộ câu hỏi có kiểu, và nó trả lời mỗi câu hỏi bằng một giá trị kèm xác suất đã hiệu chỉnh, thường trong 100 tới 200 ms:

- **Choice** chọn một lựa chọn từ một danh sách. Ví dụ: định tuyến một ticket tới billing, shipping hoặc support.
- **Score** đặt nội dung lên một thang đo mà bạn mô tả. Ví dụ: chấm một pull request từ "bỏ qua spec" tới "đáp ứng spec".
- **Noul** cho biết xác suất một mệnh đề có/không là đúng. Ví dụ: "lệnh shell này xóa file nằm ngoài dự án."

## Cài đặt

<details>
<summary><strong>Claude Code</strong></summary>

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

Chuyển từ Gemini CLI sang? Nếu `agy plugin import gemini` đã mang extension này qua, bạn vẫn nên chạy lệnh cài đặt ở trên để bản hiện tại thay thế bản đã import.

</details>

<details>
<summary><strong>Muse (muse.ai)</strong></summary>

Muse nạp skill từ `~/workspace/skills/` trên máy tính riêng của nó. Dán lệnh này vào một cuộc trò chuyện với Muse và yêu cầu Muse chạy nó:

```bash
curl -fsSL https://raw.githubusercontent.com/aaddrick/building-with-typesafe-jev/main/scripts/install_muse.sh | bash
```

Script sao chép thư mục skill vào đó và viết lại phần đầu của `SKILL.md` theo dạng Muse đọc được. Mở một cuộc trò chuyện mới. Muse nạp skill khi tác vụ phù hợp. Để cập nhật, chạy lại lệnh.

</details>

<details>
<summary><strong>Tác nhân khác có đọc SKILL.md</strong></summary>

Sao chép thư mục `skills/building-with-typesafe-jev/` vào thư mục skill của tác nhân. Giữ nguyên cả thư mục. `SKILL.md` liên kết tới các file nằm cạnh nó.

</details>

## Thiết lập API key (không bắt buộc, nên có)

Skill vẫn hoạt động khi không có key. Khi `TYPESAFE_API_KEY` được đặt trong shell của tác nhân, tác nhân có thể kiểm tra thiết kế của nó với API thật trước khi code tới dự án của bạn. Cách này bắt được tên trường sai và những câu hỏi mà Jev hiểu khác với ý bạn. Mỗi lệnh gọi tốn chưa tới một xu.

<details>
<summary><strong>Tạo, lưu trữ và xử lý sự cố key</strong></summary>

<br>

<details>
<summary><strong>Tạo key</strong> (bốn bước trong console TypeSafe)</summary>

**Bước 1.** Đăng nhập tại [console.typesafe.ai](https://console.typesafe.ai/) và mở **API Keys** ở thanh bên.

<img src="../assets/api-key/step-1.png" alt="Trang chủ console TypeSafe. Một khung và mũi tên màu hổ phách chỉ vào API Keys ở thanh bên trái." width="100%">

**Bước 2.** Nhấn **Create key** ở góc trên bên phải.

<img src="../assets/api-key/step-2.png" alt="Trang API keys. Các key hiện có bị làm mờ. Một khung và mũi tên màu hổ phách chỉ vào nút Create key ở góc trên bên phải." width="100%">

**Bước 3.** Đặt tên key theo nơi nó sẽ được dùng, chẳng hạn tên máy hoặc tên tác nhân. Sau đó nhấn **Create key**.

<img src="../assets/api-key/step-3.png" alt="Hộp thoại Create API key với tên my-coding-agent đã được nhập. Một khung và mũi tên màu hổ phách chỉ vào ô tên và nút Create key." width="100%">

**Bước 4.** Sao chép key ngay bây giờ. Console chỉ hiển thị nó một lần. Nếu làm mất, hãy tạo key mới và thu hồi key cũ.

<img src="../assets/api-key/step-4.png" alt="Hộp thoại API key created. Giá trị key bị che. Một khung và mũi tên màu hổ phách chỉ vào nút Copy." width="100%">

</details>

<details>
<summary><strong>Lưu trữ key</strong> (macOS, Linux, Windows)</summary>

Giữ key trong một file riêng mà chỉ bạn đọc được, và export nó dưới tên `TYPESAFE_API_KEY`. Tác nhân thường khởi động shell mà không có terminal, nên mỗi phần dưới đây đặt key ở nơi các shell đó nhìn thấy được. Chọn hệ thống của bạn.

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
<summary><strong>Nếu tác nhân không thấy key</strong></summary>

Yêu cầu tác nhân chạy `echo ${#TYPESAFE_API_KEY}` (hoặc `$env:TYPESAFE_API_KEY.Length` trên Windows). Nếu nó in ra `0` hoặc không in gì, hãy kiểm tra lần lượt:

- **Bạn khởi động tác nhân trước khi lưu key.** Shell của tác nhân sao chép môi trường của chương trình đã khởi động chúng. Thoát tác nhân và khởi động lại từ một terminal mới.
- **Bạn khởi động tác nhân từ dock, start menu hoặc một IDE.** Các ứng dụng đó không đọc các file shell của bạn. Xem "Ứng dụng desktop và tiện ích mở rộng IDE" ở trên.
- **Codex lọc môi trường.** Nếu `~/.codex/config.toml` đặt `include_only` trong `[shell_environment_policy]`, hãy thêm `TYPESAFE_API_KEY` vào đó. Nếu nó đặt `ignore_default_excludes = false`, Codex bỏ mọi biến có `KEY` trong tên. Hãy xóa dòng đó.
- **WSL.** Biến của Windows không truyền vào WSL. Hãy lưu key bên trong WSL theo các bước cho Linux.

</details>

</details>

## Cách kiểm thử

Chúng tôi giao cho một tác nhân lập trình sáu tác vụ Jev, chẳng hạn một hàm phân loại ticket hỗ trợ và một cổng phê duyệt cho lệnh shell. Mỗi tác vụ chạy 10 lần với skill này, không có skill, và với skill chính thức, mỗi nhóm trong một container cô lập riêng. Tác nhân có tài liệu nhưng không có API key, nên người chấm kiểm tra code nó viết. Các tiêu chí cần phán đoán được giao cho ba người chấm LLM từ ba nhà cung cấp (Claude Opus, GPT-6 Sol, Kimi K3), và đa số quyết định.

| | Không có skill | Skill này | Skill chính thức |
|---|---:|---:|---:|
| Điểm trung bình | 0.65 ± 0.05 | **0.96 ± 0.02** | 0.77 ± 0.04 |

Điểm là tỷ lệ tiêu chí đạt, lấy trung bình trên 10 lần chạy mỗi tác vụ.

**Nơi skill tạo ra khác biệt** (số lần chạy đạt trên 10):

| Code của tác nhân... | Không có skill | Skill này | Skill chính thức |
|---|---:|---:|---:|
| đếm trong code, thay vì hỏi Jev một con số | 1 | 8 | 0 |
| nêu tên một trường của đầu vào trong các câu hỏi | 0 | 10 | 1 |
| cố định hoặc ghi lại phiên bản model Jev | 0 | 10 | 0 |
| cho danh sách phòng ban một lựa chọn dành cho mọi trường hợp còn lại | 3 | 10 | 6 |
| giữ nhiều hơn một đường đi khi duyệt qua 1,200 danh mục | 1 | 10 | 7 |
| giữ một chốt chặn bằng code thuần cho các lệnh phá hủy | 7 | 10 | 2 |
| hiểu `score` là vị trí từ 0 tới n-1 | 9 | 10 | 5 |

[Xem mọi tiêu chí →](../../evals/docs/results.md#every-check)

Mỗi dòng này vượt trội so với khi không có skill, so với skill chính thức, hoặc cả hai, với mức chênh lệch quá lớn để là ngẫu nhiên ở độ tin cậy 95%.

**Chi tiết hơn:**

- [evals/README.md](../../evals/README.md): kết quả theo từng trường hợp, và cách chạy bộ eval
- [evals/docs/results.md](../../evals/docs/results.md): mọi tiêu chí, điểm của từng người chấm, chi phí, token, và phương pháp
- [evals/docs/cases.md](../../evals/docs/cases.md): sáu tác vụ và điều mà mỗi tiêu chí kiểm tra
- [evals/docs/harness.md](../../evals/docs/harness.md): cách một lần chạy hoạt động, các container cô lập, và cách giữ lại một đợt chạy
- [evals/docs/lessons.md](../../evals/docs/lessons.md): những gì đã hỏng trong lúc xây dựng bộ eval

## Bên trong có gì

Skill tải theo từng lớp, nên tác nhân chỉ đọc những gì tác vụ cần.

| File | Nội dung | Khi nào tác nhân đọc |
|---|---|---|
| `SKILL.md` | Chọn primitive nào, 11 quy tắc thiết kế, cách dùng xác suất và độ tin cậy, các lỗi thường gặp | Mọi tác vụ Jev |
| `api-reference.md` | HTTP API, SDK Python và JavaScript, giới hạn, lỗi, biến môi trường | Khi viết code |
| `patterns.md` | 4 pattern chính thức và các kỹ thuật từ 18 cookbook, kèm ngưỡng của chúng | Khi thiết kế một workflow |
| `prior-art/INDEX.md` | Bản đồ từ "thứ tôi muốn làm" tới một dạng, cùng các ý tưởng đã thất bại | Trước khi thiết kế thứ gì mới |
| `prior-art/*.md` | 11 file dạng: một đoạn code mẫu, bài học thực tế, và các dự án liên kết | Một hoặc hai file cho mỗi thiết kế |

## Thư viện tham khảo

Hầu hết các danh mục xếp dự án theo ngành. Thư viện này xếp chúng theo dạng triển khai. Một bot chơi game, một drone và một bot giao dịch có chung một dạng: vòng điều khiển. Xếp theo cách đó, cả ba dùng chung một đoạn code mẫu và một bộ bài học thực tế. 11 dạng:

- **[Vòng điều khiển](../../skills/building-with-typesafe-jev/prior-art/control-loops.md)**: game, drone, robot, thị trường.
- **[Chọn từ các ứng viên](../../skills/building-with-typesafe-jev/prior-art/select-from-candidates.md)**: tác nhân trình duyệt và điện thoại, gọi công cụ không cần LLM, trích xuất, bộ định tuyến.
- **[Cổng kiểm soát](../../skills/building-with-typesafe-jev/prior-art/gates.md)**: duyệt lệnh gọi công cụ, kiểm tra "đã xong", CI, tiền, nội dung.
- **[Bộ lọc luồng](../../skills/building-with-typesafe-jev/prior-art/stream-filters.md)**: lọc nội dung rác, kiểm duyệt, email, log, gán nhãn hàng loạt.
- **[Xếp hạng và so khớp](../../skills/building-with-typesafe-jev/prior-art/ranking-and-matching.md)**: reranker, so khớp thực thể, duyệt đồ thị và phân loại.
- **[Giám khảo và đánh giá](../../skills/building-with-typesafe-jev/prior-art/judges-and-evals.md)**: giám khảo theo rubric, chấm trace, review code để phân loại.
- **[Tăng dần và thời gian thực](../../skills/building-with-typesafe-jev/prior-art/incremental-realtime.md)**: lồng tiếng, giọng nói, giao diện chạy theo phím gõ.
- **[Ngữ cảnh và bộ nhớ của tác nhân](../../skills/building-with-typesafe-jev/prior-art/agent-context-memory.md)**: nén ngữ cảnh, cổng bộ nhớ, hết hạn bộ nhớ, điều chỉnh mức nỗ lực.
- **[Kết hợp với LLM](../../skills/building-with-typesafe-jev/prior-art/llm-pairing.md)**: planner và actor, kiểm tra rồi mới chuyển lên, chưng cất (distillation).
- **[Câu trả lời là dữ liệu](../../skills/building-with-typesafe-jev/prior-art/research-and-features.md)**: đặc trưng cho model cổ điển, công cụ nghiên cứu, benchmark.
- **[Nhúng vào hạ tầng](../../skills/building-with-typesafe-jev/prior-art/embedding-in-infrastructure.md)**: hàm SQL, cơ sở dữ liệu vector, hook CI, Home Assistant.

Chỉ mục cũng liệt kê các ý tưởng đã thất bại trong thực tế: cờ vua, review code khi Jev là người review duy nhất, nhận thức hình ảnh, và tin vào hiệu chỉnh mà không kiểm tra. Một lần thử thất bại giúp người làm sau khỏi lặp lại nó.

## Khác biệt so với skill chính thức

[Skill chính thức của TypeSafe](https://github.com/typesafe-ai/skills) là một tệp hướng dẫn thiết kế. Với chi tiết API, nó đưa tác nhân tới tài liệu trực tuyến ở mọi tác vụ. Hai skill có tên khác nhau và không xung đột, nên bạn có thể cài cả hai, dù các bài đánh giá chưa thử chúng cùng lúc.

Skill này chứa nhiều hơn ngay bên trong: hình dạng chính xác của API, các ngưỡng từ cookbook, các lỗi mà cộng đồng gặp phải, và thư viện tham khảo. Tác nhân có thể thiết kế mà không cần gọi mạng, và xem những gì người khác đã làm trước.

Jev thay đổi nhanh. Skill là bản chụp của [docs.typesafe.ai](https://docs.typesafe.ai/llms.txt) và của cộng đồng vào ngày 2026-09-25, và nó bảo tác nhân rằng tài liệu trực tuyến luôn đúng hơn khi có mâu thuẫn. Nếu một sự thật bị sai, hãy mở issue kèm liên kết tới nguồn.

## Ghi công

Các sự thật về API lấy từ tài liệu công khai và cookbook của TypeSafe AI. Phần tham khảo đến từ những người đã công bố dự án của mình, từ cộng đồng Hacker News, và từ các chỉ mục sau: [awesome-jev-typesafe](https://github.com/valentynkit/awesome-jev-typesafe), [JevDirectory](https://www.jevdirectory.org/resources), [awesome-jev-use-cases](https://github.com/walidboulanouar/awesome-jev-use-cases), và [awesome-typesafe-jev](https://github.com/AbdelStark/awesome-typesafe-jev). Mỗi file dạng đều liên kết tới các dự án gốc.

TypeSafe, Jev và System One là tên của TypeSafe AI. Dự án này chỉ dùng chúng để nói skill dùng cho việc gì.

## Giấy phép

MIT. Xem [LICENSE](../../LICENSE).
