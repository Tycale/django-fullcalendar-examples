# Create your views here.

from .forms import MyEventForm, MyRuleForm
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.template.context import RequestContext
from schedule.views import create_or_edit_event, calendar_by_periods
from django.utils import simplejson
from schedule.periods import Month
from myagenda.models import MyCalendar
from datetime import datetime
from schedule.utils import encode_occurrence
from settings import CHECK_PERMISSION_FUNC
from django.template import Context, loader

def home(request):
    calendars = MyCalendar.objects.all()
    if calendars.count() == 0:
        return HttpResponseRedirect(reverse("calendar_list"))

    return calendar_by_periods(request,
                               calendars[0].slug,
                               periods=[Month],
                               template_name='myagenda/current_month_view.html',
                               extra_context={'calendars' : calendars})


def create_event(request, calendar_slug=None):
    return create_or_edit_event(request,
                                calendar_slug=calendar_slug,
                                template_name='myagenda/event_form.html',
                                form_class=MyEventForm,
                                next='/')

def create_rule(request, template_name):
    if request.method == "POST":
        rule_form = MyRuleForm(request.POST)
        if rule_form.is_valid():
            rule_form.save()
        else:
            print rule_form.errors
    else:
        rule_form = MyRuleForm()

    return render_to_response(template_name,
                              {'rule_form':rule_form},
                              context_instance=RequestContext(request))


def coerce_start_date_dict(date_dict):
    try:
        datetime = float(date_dict.get("start"))
        datetime = datetime.fromtimestamp(datetime)
        return {'year': datetime.date.year,
                'month': datetime.date.month,
                'day': datetime.date.day,
                'hour': datetime.time.hour,
                'minute': datetime.time.minute,
                'second': datetime.time.second}
    except:
        return {}

def occurrences_to_json(occurrences, user):
    occ_list = []
    for occ in occurrences:
        original_id = occ.id
        occ_list.append({
            'id':encode_occurrence(occ),
            'title' : occ.title,
            'start' : occ.start.isoformat(),
            'end': occ.end.isoformat(),
            'read_only':not CHECK_PERMISSION_FUNC(occ, user),
            'recurring':bool(occ.event.rule),
            'persisted':bool(original_id),
            'description':occ.description.replace('\n', '\\n'),
            'allDay':False,
        })
    if occurrences : print occurrences[0].end
    return simplejson.dumps(occ_list)

def occurrences_to_html(occurences, user):
    res = ""
    for occ in occurences:
        rnd = loader.get_template('myagenda/event.html')
        resp = rnd.render(Context({'occ':occ}))
        res += resp
    return res

