(function(){
  var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var top = document.getElementById('top');
  var quick = document.getElementById('quickbar');
  var hero = document.getElementById('hero');

  // 문장을 단어 단위로 쪼개 스크롤에 맞춰 밝힌다
  var rw = document.querySelector('.reveal-words');
  var words = [];
  if (rw) {
    rw.innerHTML = rw.textContent.trim().split(/\s+/).map(function(t){
      return '<span class="w">' + t + '</span>';
    }).join(' ');
    words = [].slice.call(rw.querySelectorAll('.w'));
  }

  // 등장 애니메이션: IntersectionObserver가 안 도는 환경(숨은 탭, 일부 웹뷰)이 있어 스크롤 위치로 직접 판정한다
  var pending = [].slice.call(document.querySelectorAll('.reveal'));
  function reveal(vh){
    if (!pending.length) return;
    pending = pending.filter(function(el){
      var r = el.getBoundingClientRect();
      if (r.top < vh * .88 && r.bottom > 0) { el.classList.add('in'); return false; }
      return true;
    });
  }

  // 패럴랙스 + 헤더/상담바 상태 + 단어 밝히기
  var pars = [].slice.call(document.querySelectorAll('[data-parallax]'));
  var ticking = false;
  function frame(){
    ticking = false;
    var y = window.scrollY, vh = window.innerHeight;
    reveal(vh);
    top.classList.toggle('solid', y > 60);
    quick.classList.toggle('show', y > vh * .7);
    if (!reduce) {
      pars.forEach(function(el){
        var r = el.parentElement.getBoundingClientRect();
        if (r.bottom < -200 || r.top > vh + 200) return;
        var k = parseFloat(el.dataset.parallax);
        el.style.transform = 'translate3d(0,' + (-(r.top) * k).toFixed(1) + 'px,0)';
      });
    }
    if (words.length) {
      var r = rw.getBoundingClientRect();
      var p = (vh * .85 - r.top) / (r.height + vh * .35);
      var n = Math.round(Math.max(0, Math.min(1, p)) * words.length);
      words.forEach(function(w, i){ w.classList.toggle('on', i < n || reduce); });
    }
  }
  window.addEventListener('scroll', function(){
    if (!ticking) { ticking = true; requestAnimationFrame(frame); }
  }, { passive: true });
  window.addEventListener('resize', frame);
  frame();

  // 시술 목록 호버 시 커서를 따라다니는 사진
  var prev = document.querySelector('.proc-preview');
  var pimg = prev && prev.querySelector('img');
  var tx = 0, ty = 0, cx = 0, cy = 0, run = false;
  function follow(){
    cx += (tx - cx) * .16; cy += (ty - cy) * .16;
    prev.style.left = cx + 'px'; prev.style.top = cy + 'px';
    if (run) requestAnimationFrame(follow);
  }
  if (prev && !reduce && window.matchMedia('(hover:hover)').matches) {
    document.querySelectorAll('.proc').forEach(function(li){
      li.addEventListener('mouseenter', function(e){
        pimg.src = li.dataset.img;
        tx = cx = e.clientX + 60; ty = cy = e.clientY;
        prev.classList.add('on');
        if (!run) { run = true; follow(); }
      });
      li.addEventListener('mousemove', function(e){ tx = e.clientX + 60; ty = e.clientY; });
      li.addEventListener('mouseleave', function(){ prev.classList.remove('on'); run = false; });
    });
  }
})();
