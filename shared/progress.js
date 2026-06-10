// ESC 진행·보상 — 별(XP)·연속·주간 할당량(주3일, 미달=보통 패널티). localStorage.
// 규칙: 더 하면 OK(별 비례+보너스) / 덜하면 안됨(미달 시 연속 리셋 + 별 몰수).
(function (global) {
  var KEY = 'esc_progress';
  var QUOTA = 3;                 // 주간 필수 최소(서로 다른 학습일 수)
  var STAR_BASE = 10, STAR_FIRST_TODAY = 5, STAR_NEW_MODE = 5;
  var WEEK_BONUS = 30, WEEK_MISS_PENALTY = 20;

  function ymd(d){return d.getFullYear()+'-'+String(d.getMonth()+1).padStart(2,'0')+'-'+String(d.getDate()).padStart(2,'0');}
  function monday(d){var x=new Date(d.getFullYear(),d.getMonth(),d.getDate());var g=(x.getDay()+6)%7;x.setDate(x.getDate()-g);return ymd(x);}
  function base(){return {stars:0,streak:0,lastPlayed:null,totalSessions:0,byMode:{},badges:[],
    week:{key:null,days:[],modes:[],met:false}};}
  function load(){try{return JSON.parse(localStorage.getItem(KEY))||base();}catch(e){return base();}}
  function save(p){try{localStorage.setItem(KEY,JSON.stringify(p));}catch(e){}}
  function addBadge(p,id,cond){if(cond===undefined)cond=true;if(cond&&p.badges.indexOf(id)===-1)p.badges.push(id);}

  // 주 경계 통과 시 지난 주 마감: 할당량 미달이면 보통 패널티
  function rollover(p,now){
    var wk=monday(now);
    if(!p.week||!p.week.key){p.week={key:wk,days:[],modes:[],met:false};return p;}
    if(p.week.key!==wk){
      if(p.week.days.length<QUOTA){            // 덜함 → 안됨
        p.streak=0;
        p.stars=Math.max(0,(p.stars||0)-WEEK_MISS_PENALTY);
        p.lastMiss=p.week.key;
      }
      p.week={key:wk,days:[],modes:[],met:false};
    }
    return p;
  }

  function get(){var p=rollover(load(),new Date());save(p);return p;}

  function recordSession(modeId){
    var p=load(), now=new Date(), today=ymd(now);
    p=rollover(p,now);
    var firstToday=(p.lastPlayed!==today);
    if(firstToday){
      var y=new Date(now); y.setDate(y.getDate()-1);
      p.streak=(p.lastPlayed===ymd(y))?(p.streak+1):1;
      p.lastPlayed=today;
    }
    if(p.week.days.indexOf(today)===-1) p.week.days.push(today);
    var newMode=p.week.modes.indexOf(modeId)===-1;
    if(newMode) p.week.modes.push(modeId);

    var gained=STAR_BASE+(firstToday?STAR_FIRST_TODAY:0)+(newMode?STAR_NEW_MODE:0);
    p.stars=(p.stars||0)+gained;
    p.totalSessions=(p.totalSessions||0)+1;
    p.byMode[modeId]=(p.byMode[modeId]||0)+1;

    var justMet=false;
    if(!p.week.met && p.week.days.length>=QUOTA){ p.week.met=true; p.stars+=WEEK_BONUS; justMet=true; addBadge(p,'week-quota'); }
    addBadge(p,'first-'+modeId);
    addBadge(p,'streak-3',p.streak>=3); addBadge(p,'streak-7',p.streak>=7);
    save(p);
    return {gained:gained, justMetQuota:justMet, over:Math.max(0,p.week.days.length-QUOTA), progress:p};
  }

  // 주간 상태 요약
  function week(){var p=get();return {done:p.week.days.length,quota:QUOTA,met:p.week.met,
    over:Math.max(0,p.week.days.length-QUOTA),stars:p.stars||0,streak:p.streak||0};}

  global.ESCProgress={get:get,recordSession:recordSession,week:week,QUOTA:QUOTA};
})(window);
