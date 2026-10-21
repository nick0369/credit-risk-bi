/* Aggregated public source data only: no account-level records shipped to browser. */
const data = window.PORTFOLIO;
const $ = id => document.getElementById(id);
const number = value => new Intl.NumberFormat('en-US', {maximumFractionDigits: 0}).format(value);
const compact = value => new Intl.NumberFormat('en-US', {notation:'compact', maximumFractionDigits:2}).format(value);
const pct = value => `${(100 * value).toFixed(2)}%`;
const total = (rows, field) => rows.reduce((sum, row) => sum + row[field], 0);
const ratio = (a,b) => b ? a/b : 0;
function filtered(){return data.segments.filter(s => ($('risk').value==='all'||s.risk===$('risk').value)&&($('band').value==='all'||s.band===$('band').value));}
function render(){
 const rows=filtered(), n=total(rows,'accounts'), balance=total(rows,'balance'), limits=total(rows,'limits');
 const cards=[['Accounts',number(n),'Distinct accounts in selected segments'],['Positive billed balance',`NT$ ${compact(balance)}`,'September 2005 · negative bills floored at zero'],['Observed default rate',pct(ratio(total(rows,'defaults'),n)),'Single next-month outcome'],['Weighted utilization',pct(ratio(balance,limits)),'Positive balances / credit limits']];
 $('cards').innerHTML=cards.map(([label,value,note])=>`<div class="card"><small>${label}</small><strong>${value}</strong><span>${note}</span></div>`).join('');
 const risks=[...new Set(rows.map(r=>r.risk))];
 $('bars').innerHTML=risks.map(risk=>{const group=rows.filter(r=>r.risk===risk),rate=ratio(total(group,'defaults'),total(group,'accounts'));return `<div class="bar-row"><div class="bar-title"><span>${risk}</span><strong>${pct(rate)}</strong></div><div class="track"><div class="fill" style="width:${100*rate}%"></div></div></div>`;}).join('');
 $('rows').innerHTML=rows.map(r=>`<tr><td>${r.risk}</td><td>${r.band}</td><td>${number(r.accounts)}</td><td>${pct(ratio(r.defaults,r.accounts))}</td><td>NT$ ${compact(r.balance)}</td><td>${pct(ratio(r.balance,r.limits))}</td></tr>`).join('');
 $('pdValue').textContent=`${$('pd').value}%`; $('lgdValue').textContent=`${$('lgd').value}%`;
 $('loss').textContent=`NT$ ${compact(balance * Number($('pd').value)/100 * Number($('lgd').value)/100)}`;
}
if(!data) throw Error('Missing dashboard data: run credit-risk build');
const maximum=Math.max(...data.history.map(r=>Math.max(r.bill,r.payment)));
$('historyChart').innerHTML='<p class="footnote">Teal: billed amount · Gray: payment amount</p>'+data.history.map(r=>`<div class="history-row"><span>${r.statement_month.slice(0,7)}</span><div class="history-bars"><div class="bill" style="width:${100*r.bill/maximum}%"></div><div class="payment" style="width:${100*r.payment/maximum}%"></div></div><span class="history-value">${compact(r.bill)}<br>${compact(r.payment)}</span></div>`).join('');
$('checks').innerHTML=data.validation.checks.map(c=>`<span class="check">${c.passed?'✓':'✕'} ${c.check.replaceAll('_',' ')}</span>`).join('');
$('build').textContent=`${number(data.validation.accounts)} accounts · ${number(data.validation.account_months)} account-months · Built ${data.validation.built_at_utc} · Source SHA-256: ${data.validation.source_sha256}`;
['risk','band','pd','lgd'].forEach(id=>$(id).addEventListener('input',render));
$('reset').onclick=()=>{$('risk').value='all';$('band').value='all';render();};
$('download').onclick=()=>{const rows=filtered(),fields=Object.keys(rows[0]||{}),csv=[fields.join(','),...rows.map(r=>fields.map(f=>JSON.stringify(r[f])).join(','))].join('\n');const link=document.createElement('a');link.href=URL.createObjectURL(new Blob([csv],{type:'text/csv;charset=utf-8;'}));link.download='credit-risk-segments.csv';link.click();setTimeout(()=>URL.revokeObjectURL(link.href),1000);};
render();
