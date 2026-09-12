from pathlib import Path
from dataclasses import replace
import json
from dominant_circuit import (Investigation, DecisionDescription, WorkingAccount, Boundary,
    ObservationPlan, PossibleFinding, Observation, ConsequentialInput, AnalyticalResult)
from dominant_circuit.core.investigation import AccountRelationship, ParticipantPosition
from dominant_circuit.core.evidence import encode, decode

OUT=Path('/private/tmp/dc-stage0-forward-test')
trace=[]
turns=[]

def save(label,i):
    payload=encode(i)
    restored=decode(json.loads(json.dumps(payload)))
    assert restored.render_fields()==i.render_fields()
    trace.append({'stage':label,'state':payload})
    return i

def actual(name,value,context,participant,plan=None,missing=(),limits=()):
    return Observation(ConsequentialInput(name,value,origin='user_report',
        evidence_ref='synthetic:user-turn:'+name,scope='support-queue'),context,
        missingness=missing,selection_limits=limits,raw_episode_ref='synthetic:episode:'+name,
        plan_ref=plan,reported_by=participant)

def finish(n,user,lead,i):
    response=lead+'\n\n'+i.to_markdown()
    turns.append({'turn':n,'user':user,'host_response':response,'workflow':i.workflow,
        'current_model_ref':i.current_model_ref,'current_goal_ref':i.current_goal_ref,
        'pending_reviews':list(i.pending_reviews),'contested_goals':i.contested_goals,
        'six_fields':i.render_fields(),'last_update':i.last_update()})
    (OUT/f'turn-{n}-state.json').write_text(json.dumps(encode(i),indent=2))
    return save(f'turn-{n}-delivered',i)

u1='Our support queue got slower after hiring three people. Where should I look?'
i=Investigation.begin('support-queue',DecisionDescription('support-queue',
    'Where should we look to understand a reported support slowdown after hiring three people?',
    objectives=['Understand the reported slowdown and choose a feasible next observation'],
    uncertainties=['Slower could mean first reply, handling, closure, or durable resolution',
                   'Before/after timing does not establish a hiring effect']), 'synthetic:user-turn:1')
i=i.record_position('user',ParticipantPosition('user','Understand why support got slower',
    agreement='adopted',role='support participant; exact role unknown'), 'synthetic:user-turn:1')
i=i.propose_account('capacity',WorkingAccount('Capacity and coordination',
    ('hiring','training time','handoffs','time until a useful response'),
    Boundary(('support staffing','training','handoffs'),('new demand','unresolved product defects'),
        ('definition of slower','case mix','repeat contacts'),
        'A staffing-only account could miss changes in demand or count closures as resolutions.',
        visible_observations=('user-reported hiring and slowdown',),
        outside_observation='Compare whether delayed episodes were first requests or repeats',outside_access='unknown'),
    ('Training or coordination may temporarily consume experienced staff time',), proposed_by='host'),
    'synthetic:host:turn-1-capacity')
i=i.propose_account('demand',WorkingAccount('Demand and case mix',
    ('new requests','repeat requests','case complexity'),
    Boundary(('incoming support work','case complexity'),('product repair process',),
        ('repeat-contact causes','volume change'),
        'Contacts and underlying problems may not be the same unit.',
        outside_observation='Look for a repeated underlying issue in an available episode',outside_access='unknown'),
    ('More requests, repeated requests, or harder cases may offset extra staff',),proposed_by='host'),
    'synthetic:host:turn-1-demand')
i=i.relate_accounts('capacity-demand',AccountRelationship(
    (i.latest_ref('account','capacity'),i.latest_ref('account','demand')),'complementary',
    'Capacity pressure and demand changes can coexist; neither is established by timing alone'),
    'synthetic:host:turn-1-relationship')
i=i.record_analysis('boundary-check',AnalyticalResult('Meaning of the support slowdown',
    'Qualitative comparison of capacity and demand boundaries','relevant',
    'Separate processing constraints from incoming work and clarify the outcome being counted',
    reason='The user describes changing work over time, so a limited systems boundary is useful',
    limitations=('No rates, formal dynamic model, intervention estimate, or causal identification available',)),
    (i.latest_ref('account','capacity'),i.latest_ref('account','demand')),'synthetic:host:turn-1-analysis')
plan=ObservationPlan('Compare delayed first-time requests with repeated issues around the hiring period',
    'exploratory',(i.latest_ref('account','capacity'),i.latest_ref('account','demand')),
    ('Comparable meanings of slower before and after hiring',),
    'Ticket histories only if already accessible within the user\'s role',
    'For a small existing sample, distinguish first response, closure and durable resolution; note handoffs and repeat reasons',
    (PossibleFinding('coordination','Delays occur around training or handoffs','Capacity/coordination deserves closer observation; demand remains possible'),
     PossibleFinding('repeats','The same underlying issue returns','Expand the boundary to recurrence causes; do not infer how prevalent it is'),
     PossibleFinding('both','Both patterns appear','Keep complementary mechanisms; relative contributions remain unknown'),
     PossibleFinding('inconclusive','No accessible comparable episodes or no clear pattern','Use one voluntarily recalled episode to clarify the unit; pause any inaccessible comparison')),
    access='unknown',owner=None,effort='A few already accessible episodes',delay=None,
    collection_effects='Retrospective reading should not change workflow; selection may favor memorable cases',
    omission_challenge='Look beyond closures and handling time to whether the underlying issue returned')
i=i.propose_observation('ticket-comparison',plan,'synthetic:host:turn-1-plan')
i=i.close_cycle('A bounded comparison is identified, with access unresolved and a recollection fallback',
    'synthetic:host:turn-1-stop')
i=finish(1,u1,'Start by separating time spent handling work from work that keeps coming back. Hiring can coincide with more training and handoffs, but the timing alone does not tell us the cause. If ticket histories are already available to you, compare a few delayed cases using the same meaning of “slower.” If they are not, one episode you remember can still help.',i)

u2='I asked two colleagues. They say people repeatedly contact us about bugs that never get fixed. I cannot access the ticket-level logs, and the manager wants us to focus only on closing more tickets.'
i=i.reopen('synthetic:user-turn:2')
i=i.receive_observation('colleagues',actual('colleagues',
    'User reports two colleagues say people repeatedly contact support about bugs that never get fixed',
    'Unplanned secondhand report; colleagues, time period, and underlying episodes are unspecified',
    'user relaying two colleagues',missing=('Ticket-level logs are unavailable to the user',
        'No counts, denominator, timestamps, or independently verified repair status'),
    limits=('Two consulted colleagues are a selected source','The same underlying experience may be shared by both colleagues')))
i=save('turn-2-evidence-pending',i)
i=i.review_observation('colleagues','inconclusive',{'capacity':'unchanged','demand':'unresolved'},
    ('unresolved_evidence',),
    'The report makes unresolved-bug recurrence worth representing, but neither its prevalence nor its contribution to the slowdown is established; this was not the planned ticket comparison',
    'synthetic:host:turn-2-review')
i=i.record_position('user',ParticipantPosition('user','Understand why support got slower',
    agreement='adopted',can_access=False,role='Cannot access ticket-level logs; other access unknown'),
    'synthetic:user-turn:2-access')
i=i.record_position('manager',ParticipantPosition('manager (as reported by user)',
    'Focus only on closing more tickets',agreement='unresolved',role='Manager; authority scope unknown'),
    'synthetic:user-turn:2-manager-goal')
i=i.propose_observation('ticket-comparison',replace(plan,accounts=(i.latest_ref('account','capacity'),i.latest_ref('account','demand')),
    access='unavailable'),'synthetic:user-turn:2-no-log-access')
i=save('turn-2-inaccessible-plan',i)
old=i.get(i.latest_ref('account','demand'))
i=i.revise_account('demand',replace(old,name='Recurring unresolved issues',
    boundary=Boundary(('support contacts','underlying product issues','reported persistence of bugs'),
        ('product repair ownership and priorities',),('actual repair status','recurrence prevalence','time consumed by returns'),
        'Colleague reports may concentrate on frustrating cases; user-level recurrence and queue-wide rates remain distinct.',
        visible_observations=('secondhand report from two colleagues',),
        outside_observation='An existing recalled episode can show what the person needed after a closure',outside_access='available'),
    mechanisms=('An unresolved issue may bring the same person back for further support work',),
    assessment='unassessed',assessment_scope='',working_use_event=None),
    ('boundary_revision','mechanism_revision'),i.latest_ref('obs','colleagues'),
    'Include product issue persistence as a possible source of repeat work, retaining the limited secondhand evidence')
i=i.relate_accounts('capacity-demand',AccountRelationship((i.latest_ref('account','capacity'),i.latest_ref('account','demand')),
    'complementary','Repeat work may coexist with training and handoff costs; the reports do not settle either contribution'),
    'synthetic:host:turn-2-relationship')
recollection=ObservationPlan('Describe one already remembered repeat-contact episode and distinguish the contact from the underlying issue',
    'descriptive',(i.latest_ref('account','capacity'),i.latest_ref('account','demand')),(),
    'User\'s voluntary recollection, without consulting records or contacting anyone',
    'Write a short sequence: request, response or closure, and reason for returning; mark unknown details',
    (PossibleFinding('return','A person returns about the same underlying issue','Preserve the episode; separate contact/reopen events from distinct problems before interpreting closure totals'),
     PossibleFinding('new-issue','The return concerns a genuinely different issue','Do not count this episode as recurrence of one unresolved issue'),
     PossibleFinding('inconclusive','The reason or sequence cannot be recalled','Keep the cause unresolved and pause until an accessible concrete episode is offered')),
    access='available',owner='user if they choose to describe a memory',effort='One short recollection',delay='Now if recalled',
    collection_effects='Recall may omit steps and favor unusual cases; no workflow change',
    omission_challenge='Include what remained unresolved rather than only whether a ticket was closed')
i=i.propose_observation('recalled-episode',recollection,'synthetic:host:turn-2-plan')
i=i.close_cycle('An accessible descriptive next step avoids relying on unavailable logs', 'synthetic:host:turn-2-stop')
i=finish(2,u2,'That gives us a concrete possibility: unresolved issues may be bringing work back into the queue. It does not show how much of the slowdown they explain. Ticket-level comparison is blocked by your access. The next useful step is a short account of one repeat-contact episode you already remember: what the person needed, what happened, and why they returned. Mark anything you do not know. Your manager’s closure target is recorded separately from your question about delay; we have not established agreement between those goals.',i)

u3='I am not sure your diagram fits. Yesterday one person reopened the same issue five times. Can you just tell me what to do next?'
i=i.reopen('synthetic:user-turn:3')
i=i.record_correction('diagram-fit','disputed_interpretation',
    'I am not sure your diagram fits. Yesterday one person reopened the same issue five times.',
    'user','synthetic:user-turn:3-fit')
i=i.receive_observation('five-reopens',actual('five-reopens',
    'Yesterday one person reopened the same issue five times',
    'One user-reported episode from yesterday in the synthetic scenario; who reopened and why are unspecified',
    'user',plan=i.latest_ref('plan','recalled-episode'),
    missing=('Who the person is and whether they are a customer or staff member are unspecified',
        'The five reopen reasons, repair status, time spent, and queue-wide frequency are unknown'),
    limits=('A single memorable episode cannot establish queue-wide prevalence or hiring effects',)))
i=save('turn-3-evidence-and-correction-pending',i)
i=i.review_observation('five-reopens','return',{'capacity':'not_assessed','demand':'unresolved'},
    ('unresolved_evidence',),
    'The episode fits the descriptive return outcome and separates five reopening events from one reported issue; it does not establish that the bug remained unfixed or explain the queue slowdown',
    'synthetic:host:turn-3-review')
i=i.acknowledge_correction('diagram-fit',
    'Use the concrete sequence instead of requiring the user to adopt a diagram. Five reopenings are not five distinct issues; their cause remains unknown.',
    'synthetic:host:turn-3-ack')
old=i.get(i.latest_ref('account','demand'))
i=i.revise_account('demand',replace(old,name='One issue, potentially repeated support work',
    variables=('distinct underlying issues','reopening events','reason for reopening','unresolved need'),
    boundary=Boundary(('underlying issue','reopening events','support responses'),('product repair process',),
        ('reopen reasons','identity or role of reopener','whether closure counted as resolution','representativeness'),
        'One issue can generate several events, and an event does not establish a new issue or a confirmed unresolved defect.',
        visible_observations=('one person reportedly reopened the same issue five times yesterday',),
        outside_observation='Recall what changed, or remained unmet, between reopening events',outside_access='available'),
    mechanisms=('A still-unmet need may produce repeated events; administrative reopening or another cause remains possible',),
    assessment='unassessed',assessment_scope='',working_use_event=None),
    ('boundary_revision','unresolved_evidence'),i.latest_ref('correction','diagram-fit'),
    'Make event versus issue explicit in response to the user\'s mismatch, without silently changing historical metrics')
i=i.relate_accounts('capacity-demand',AccountRelationship((i.latest_ref('account','capacity'),i.latest_ref('account','demand')),
    'unresolved','Repeated events and capacity costs may coexist, but the single episode does not tell us why events occurred or how much work they created'),
    'synthetic:host:turn-3-relationship')
next_plan=replace(recollection,question='Write the remembered sequence for yesterday’s one issue, keeping unknown reopen reasons explicit',
    accounts=(i.latest_ref('account','capacity'),i.latest_ref('account','demand')),
    method='Create one row per remembered reopening: what preceded it and what remained unmet. Keep one underlying issue distinct from five reported events; leave unknown rows blank',
    possible_findings=(PossibleFinding('unmet','The same need remained unmet across reopenings','Keep unresolved-need recurrence plausible for this episode; broader impact stays unknown'),
        PossibleFinding('administrative','Reopens were administrative or the underlying need changed','Revise the episode explanation; do not infer persistent defects from reopen counts'),
        PossibleFinding('inconclusive','Reasons cannot be recalled','Stop here and retain the episode; reopen the investigation if an accessible explanation becomes available')),
    effort='A two-minute private note from memory',collection_effects='Memory can be incomplete; this is a suggestion for reflection, not an instruction to collect restricted records or change workflow')
i=i.propose_observation('episode-sequence',next_plan,'synthetic:host:turn-3-next')
i=i.close_cycle('One concrete next step is enough; do not require a further framing exercise', 'synthetic:host:turn-3-stop')
i=finish(3,u3,'You do not need to make the diagram fit. Next, spend two minutes writing yesterday’s episode from memory: one underlying issue, five reported reopening events, and whatever you remember happening between them. Leave unknown reasons blank. This will help distinguish an unmet need from administrative reopening or another cause. If you cannot recall the sequence, stop there and keep the example as unresolved. No additional data collection is needed for this step.',i)

(OUT/'trace.json').write_text(json.dumps(trace,indent=2))
(OUT/'turns.json').write_text(json.dumps(turns,indent=2))
(OUT/'transcript.md').write_text('# Synthetic independent forward test\n\nThis is one synthetic forward test, not a live-host reliability study or human release signoff. No records were collected, people contacted, or interventions performed.\n\n'+ '\n\n'.join(f'## Turn {t["turn"]}\n\n**User:** {t["user"]}\n\n**Host:** {t["host_response"]}\n\n**State update:** {t["last_update"]}' for t in turns))
assert all(not s['state']['fields']['pending_reviews']['items'] for s in trace if s['stage'].endswith('delivered'))
assert len(i.observations)==2
assert len([r for r in i.records if r.kind=='correction'])==1
assert all(not getattr(r.payload,'authorization_event',None) for r in i.records if r.kind=='plan')
assert i.contested_goals
assert not any(r.kind in {'handoff','report'} for r in i.records)
print(json.dumps([{'turn':t['turn'],'workflow':t['workflow'],'model':t['current_model_ref'],'pending_reviews':t['pending_reviews'],'contested_goals':t['contested_goals']} for t in turns],indent=2))
print(f'Wrote {len(trace)} state snapshots and {len(turns)} host responses to {OUT}')
