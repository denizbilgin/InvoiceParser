# Invoice Parser & Analyzer
Birleşik Gümrük Müşavirliği – Makine Öğrenmesi Mühendisi Pozisyonu İçin Hazırlanmıştır

Deniz Bilgin - denizbilgin156@gmail.com

## Proje Hakkında
- Bu projeyi geliştirirken clean code prensiplerini takip ederek soyutlama teknikleriyle sürdürülebilir ve kolay güncellenebilir bir yapı oluşturdum.
- Projeyi 3 ana bileşene ayırdım ve her birini bağımsız şekilde tasarlayıp geliştirdim:
  - Reader'lar (PDF'lerden OCR kullanarak metin okuma),
  - Analyzer'lar (mantıksal gruplama),
  - Validator'lar (doğrulama ve nihai raporun oluşturulması).
- Her aşamada elde ettiğim çıktıyı inceleyebilmeniz için onları `outputs` klasörünün içine export ettim.
- Yorum satırları ve docstring'ler kullanarak, koda ilk defa bakan birinin bile kodu anlayabilmesi için uğraştım.
- Geliştirdiğim sistem, otomatik olarak hatalı ve eksik faturaları detaylı olarak analiz ediyor ve bunları final raporunda belirtip detaylandırıyor.
 
### Readers
- Reader sınıflarını oluştururken birden fazla kütüphane kullandım ve otomatik olarak bunların sonuçlarını karşılaştıran ve en iyi sonucu seçen bir sistem hazırladım.. Böylece her dosya için en iyi metni seçebileceğim alternatifler oluşturdum.
- Factory Pattern kullanarak PDF türünü (scanned veya klasik PDF) otomatik olarak tespit eden ve buna göre işlem yapmamızı sağlayan otomatize edilmiş bir sistem de geliştirdim.

### Analyzers
- Projenin bu aşaması için çok çeşitli araçlar denedim; ancak yapay zekânın gücü olmadan, aşırı esnek bir fatura gruplama sistemi yazmak oldukça zor bir iştir.
- Bu aşamada BERT modelini denedim; fakat sınırlı sayıda fatura örneği ile fine-tune ettiğim BERT modelinin başarısı oldukça kötüydü.
- Bu nedenle, bir yapay zeka mühendisi olarak burada LLM'lerin gücünden faydalanmaya karar verdim.
- Mülakatta LLM'leri veri güvenliği nedeniyle kullanmak istemediğinizden bahsetmiştiniz. Projenin bu aşamasında, bilgisayarıma indirip yerel olarak çalıştırdığım LLM'leri bu görev için kullandım.
- Lokal ortamda çalışan LLM'ler herhangi bir yere veri göndermediği ve tamamen yazılımcının kontrolü altında olduğu için en güvenli yöntemdir.
- Bu aşama için LLM seçerken şu modelleri test ettim:
  - DeepSeek r1:1.5B
  - DeepSeek r1:7B
  - DeepSeek r1:14B
  - Mistral 7B-Instruct
- LLM boyutu büyüdükçe elde edilen sonucun doğruluğu da artıyor; fakat aynı zamanda modeli çalıştırmak için gereken sistem gereksinimleri de artıyor. Yani daha güçlü bir bilgisayar ile daha büyük bir LLM kullanarak hem daha hızlı hem de daha doğru sonuçlar elde etmek mümkün.
- Analyzer'lar için LLM'leri, prompt mühendisliği teknikleri ile mantıksal gruplama aracı olarak kullandım ve bu adımın sonunda tek tip, detaylı ve yüksek doğruluklu bir sonuçlar elde ettim.

### Validators
- Bu kısım, geliştirdiğim projenin case’in isterlerini karşılayıp karşılamadığını ölçen; faturada hatalar varsa bunları tespit edip raporlayan ve her bir fatura için final raporunu otomatik olarak oluşturan bir yapıya sahiptir.

## Kurulum
- Projeyi kendi ortamınızda ayağa kaldırmak için, LLM’leri lokalinizde çalıştırabilmenizi sağlayan Ollama uygulamasını indirmeniz gerekiyor.
- İndirdikten sonra `ollama pull mistral:7b-instruct` komutunu yazarak, benim son olarak kullanmaya karar kıldığım modeli indirebilirsiniz.
- Son olarak `main.py` dosyasını çalıştırarak, istediğiniz faturayı otomatik olarak analiz ve rapor eden yazılımı başlatabilirsiniz.


