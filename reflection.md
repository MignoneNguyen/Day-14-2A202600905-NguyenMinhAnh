# Evaluation Report & Reflection

## 1. 3 Worst Failures Analysis (5 Whys Method)

### Failure 1: Hallucination (Score: Faithfulness = 0.11)
- **Symptom:** AI Agent sinh ra câu trả lời chứa thông tin không hề có trong ngữ cảnh (context) được cung cấp.
- **Why 1:** Tại sao lại có thông tin này? -> Vì agent cố gắng tự đoán câu trả lời dựa trên kiến thức nội bộ (internal knowledge) thay vì đọc context.
- **Why 2:** Tại sao agent lại dùng internal knowledge? -> Vì context trả về không chứa đủ thông tin để trả lời câu hỏi.
- **Why 3:** Tại sao context trả về không đủ thông tin? -> Vì retriever (bộ tìm kiếm) lấy ra các chunk tài liệu không liên quan (Context Recall thấp).
- **Why 4:** Tại sao retriever lấy sai chunk? -> Vì độ tương đồng ngữ nghĩa giữa câu hỏi của user và tài liệu bị sai lệch do câu hỏi quá ngắn hoặc thiếu ngữ cảnh.
- **Why 5:** Tại sao không có guardrail chặn lại? -> Vì chúng ta chưa triển khai cơ chế kiểm tra (Hallucination Checker / Self-Correction) ở bước cuối.
- **Root Cause:** Retriever yếu kém do không có Query Expansion và thiếu cơ chế Guardrail chặn hallucination trước khi output.

### Failure 2: Irrelevant (Score: Relevance = 0.20)
- **Symptom:** Trả lời lạc đề, nói vòng vo nhưng không đi thẳng vào câu hỏi chính.
- **Why 1:** Tại sao trả lời lạc đề? -> Vì Prompt yêu cầu "trả lời dựa trên context" nhưng lại không nhấn mạnh "trả lời trực tiếp câu hỏi".
- **Why 2:** Tại sao prompt không đủ chặt chẽ? -> Vì chưa cung cấp Few-shot examples (các ví dụ mẫu) cho agent.
- **Why 3:** Tại sao thiếu ví dụ mẫu? -> Do đang dùng một system prompt chung chung cho mọi loại câu hỏi (Routing kém).
- **Root Cause:** Prompt Design thiếu chặt chẽ (ambiguous prompt) và thiếu cơ chế Intent Routing.

### Failure 3: Incomplete (Score: Completeness = 0.22)
- **Symptom:** Câu trả lời bị thiếu hụt rất nhiều thông tin quan trọng so với Expected Answer.
- **Why 1:** Tại sao thiếu thông tin? -> Do thông tin bị cắt đứt giữa chừng trong lúc generation hoặc do chỉ lấy một phần context.
- **Why 2:** Tại sao chỉ lấy được một phần context? -> Do Chunk Size quá nhỏ (ví dụ 200 tokens) khiến một ý hoàn chỉnh bị chia cắt làm 2 chunk khác nhau.
- **Why 3:** Tại sao chia cắt làm 2 chunk nhưng retriever chỉ lấy 1? -> Vì `top_k` đang set quá thấp (ví dụ top_k = 2) nên không lấy được chunk còn lại.
- **Root Cause:** Chunking Strategy chưa tối ưu (thiếu overlap, chunk size quá nhỏ) kết hợp với giới hạn `top_k` nghiêm ngặt.

---

## 2. Improvement Log

Dựa trên phân tích 5 Whys trên, đây là kế hoạch cải thiện:

| Failure ID | Type | Root Cause | Suggested Fix | Status |
|------------|------|------------|---------------|--------|
| F001 | Hallucination | Retriever yếu, thiếu Guardrail chặn output bịa đặt | Triển khai Query Expansion (thêm từ khóa) và Thêm bước Post-check (Self-Correction) bằng LLM-as-Judge nhỏ để chặn hallucination. | Open |
| F002 | Irrelevant | Prompt chung chung, không có ví dụ mẫu, routing kém | Bổ sung Few-shot prompting, xây dựng Router phân loại Intent trước khi đưa vào Generator. | Open |
| F003 | Incomplete | Chunk size quá nhỏ làm vỡ ngữ cảnh, top_k thấp | Tăng Chunk Size lên 500-1000 tokens với Overlap 10%, và tăng `top_k` lên 5. Thêm kĩ thuật Parent Document Retriever. | Open |

---

## 3. CI/CD & Regression Strategy

Để đảm bảo chất lượng hệ thống AI không bị suy giảm (regression) theo thời gian, chiến lược kiểm thử CI/CD được thiết lập như sau:

1. **Trigger CI/CD:** Hệ thống Evaluation sẽ được chạy tự động mỗi khi:
   - Có thay đổi trong System Prompt.
   - Có thay đổi trong mô hình Embedding hoặc chiến lược Chunking/Retriever.
   - Định kỳ hàng tuần để kiểm tra Data Drift (dữ liệu mới làm hỏng retriever).

2. **Quality Gates (Ngưỡng chốt chặn):**
   - **Pass Rate:** Ít nhất 90% test cases trong Golden Dataset phải đạt điểm Pass (cả 3 metrics >= 0.5).
   - **No Regression Rule:** Tính trung bình từng metric (Faithfulness, Relevance, Completeness). Nếu có bất kỳ metric nào giảm lớn hơn `0.05` so với phiên bản (baseline) trước đó trên production -> **Chặn Deploy (Block Deployment)**.
   - **Toxicity/Safety:** Yêu cầu các Adversarial cases phải bị chặn 100% (Refusal = True).

3. **Cơ sở hạ tầng CI/CD:**
   - Sử dụng GitHub Actions. Script sẽ kéo Golden Dataset, chạy agent local hoặc gọi qua test endpoint, lấy kết quả chấm điểm.
   - Nếu `BenchmarkRunner.run_regression()` trả về `passed=False`, GitHub Actions run sẽ `exit(1)` (Fail). Mọi pull request sẽ không được phép merge cho đến khi fix xong.
   - Báo cáo Benchmark sẽ tự động comment vào Pull Request để Reviewer xem xét.
