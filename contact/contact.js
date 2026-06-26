document.getElementById('contactForm').addEventListener('submit', function (e) {
  e.preventDefault();

  var name = document.getElementById('f-name').value.trim();
  var phone = document.getElementById('f-phone').value.trim();
  var hospital = document.getElementById('f-hospital').value.trim();
  var dept = document.getElementById('f-dept').value.trim();
  var url = document.getElementById('f-url').value.trim();
  var msg = document.getElementById('f-msg').value.trim();

  var body = [
    '이름: ' + name,
    '연락처: ' + phone,
    '병원명: ' + (hospital || '-'),
    '진료과목: ' + (dept || '-'),
    '홈페이지주소: ' + (url || '-'),
    '',
    '문의내용:',
    msg
  ].join('\n');

  var subject = '[꿈을담은에이전시 문의] ' + (hospital || name);
  var mailto = 'mailto:biniare@gmail.com?subject=' + encodeURIComponent(subject) + '&body=' + encodeURIComponent(body);

  window.location.href = mailto;
});
