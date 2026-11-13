/* Shared app bar + theme for every tool page.
   Usage (in <head>, after the page's own <style>):
     <link rel="stylesheet" href="../assets/ui.css">
     <script src="../assets/ui.js" data-section="Tiếng Nhật" data-title="Kanji Game"></script>
   - Applies the saved theme before first paint (key: uiTheme = "light" | "dark").
   - Inserts a sticky bar: ← Trang chủ · Section / Title · theme toggle.
   - Fires window event "ui-theme-change" so pages (e.g. the 3D game) can repaint. */
(function(){
  "use strict";
  var me = document.currentScript;
  var KEY = "uiTheme";
  var root = document.documentElement;
  function get(){ try{ return localStorage.getItem(KEY); }catch(e){ return null; } }
  function set(v){ try{ localStorage.setItem(KEY, v); }catch(e){} }
  function apply(t){
    if (t === "light" || t === "dark"){ root.setAttribute("data-theme", t); root.setAttribute("data-t", t); }
    else { root.removeAttribute("data-theme"); root.removeAttribute("data-t"); }
  }
  function effective(){
    var t = root.getAttribute("data-theme");
    if (t) return t;
    return (window.matchMedia && matchMedia("(prefers-color-scheme: dark)").matches) ? "dark" : "light";
  }
  apply(get());   // before paint

  // Site root = folder that holds /assets/ui.js
  var base = (me && me.src) ? me.src.replace(/assets\/ui\.js(\?.*)?$/, "") : "/";
  var section = (me && me.getAttribute("data-section")) || "";
  var title = (me && me.getAttribute("data-title")) || document.title;
  var host = (me && me.getAttribute("data-host")) || "";   // optional CSS selector to put the bar into

  // favicon shared with the main site
  if (!document.querySelector('link[rel~="icon"]')){
    var ic = document.createElement("link"); ic.rel = "icon"; ic.type = "image/png";
    ic.href = base + "icons/favicon-32.png"; document.head.appendChild(ic);
  }

  function esc(s){ return String(s).replace(/[&<>"]/g, function(c){ return {"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]; }); }

  function build(){
    if (document.querySelector(".ui-bar")) return;
    var bar = document.createElement("nav");
    bar.className = "ui-bar";
    bar.setAttribute("aria-label", "Điều hướng");
    bar.innerHTML =
      '<a class="ui-home" href="' + esc(base) + '#/" title="Về trang chủ">← <span class="ui-home-label">Trang chủ</span></a>' +
      '<span class="ui-crumb">' + (section ? esc(section) + " / " : "") + "<b>" + esc(title) + "</b></span>" +
      '<button type="button" class="ui-theme" aria-label="Đổi giao diện sáng/tối"></button>';
    var btn = bar.querySelector(".ui-theme");
    function label(){ btn.textContent = effective() === "dark" ? "☀️ Sáng" : "🌙 Tối"; }
    label();
    btn.addEventListener("click", function(){
      var next = effective() === "dark" ? "light" : "dark";
      set(next); apply(next); label();
      try{ window.dispatchEvent(new CustomEvent("ui-theme-change", { detail: next })); }catch(e){}
    });
    if (window.matchMedia) matchMedia("(prefers-color-scheme: dark)").addEventListener("change", label);

    var target = host ? document.querySelector(host) : null;
    if (target){ target.insertBefore(bar, target.firstChild); bar.style.position = "static"; bar.style.margin = "0 0 10px"; return; }

    var body = document.body;
    body.insertBefore(bar, body.firstChild);
    body.classList.add("ui-has-bar");
    // Stretch the bar edge to edge even when the page body has padding.
    var cs = getComputedStyle(body);
    var pl = parseFloat(cs.paddingLeft) || 0, pr = parseFloat(cs.paddingRight) || 0, pt = parseFloat(cs.paddingTop) || 0;
    bar.style.marginLeft = (-pl) + "px";
    bar.style.marginRight = (-pr) + "px";
    bar.style.marginTop = (-pt) + "px";
    bar.style.width = "calc(100% + " + (pl + pr) + "px)";
    bar.style.alignSelf = "stretch";
    if (cs.display.indexOf("flex") >= 0 && cs.flexDirection.indexOf("row") === 0){ body.style.flexWrap = "wrap"; body.style.alignContent = "flex-start"; bar.style.flex = "0 0 auto"; bar.style.alignSelf = "flex-start"; }
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", build);
  else build();
})();
