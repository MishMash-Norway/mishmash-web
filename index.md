<div style="float:right;margin:0 0 1rem 1rem;">
    <img src="/assets/images/bubbles/mishmash_bubbles.svg" alt="MishMash explores the meeting point of humans and machines with art and science" width="400">
</div>

MishMash is a Norwegian AI centre comprising more than 200 researchers from higher education institutions in Norway, in collaboration with numerous public and private sector partners. The primary objective of MishMash is to **create, explore, and reflect on AI for, through, and in creative practices**. MishMash researchers will investigate AI’s impact on creative processes, develop innovative co-creative AI systems and educational strategies, and address AI’s ethical, cultural, legal, and societal implications in creative domains.


## Vacancies

- We have several [fully-funded PhD and PostDoc fellowships](https://mishmash.no/news/positions/) available in various MishMash partner institutions in Norway.

<h1>Events</h1>
{% assign all_events = site.events | where_exp: "item", "item.draft != true" %}
{% assign future_events = all_events | where_exp: "item", "item.date >= site.time" | sort: 'date' %}
{% assign past_events = all_events | where_exp: "item", "item.date < site.time" | sort: 'date' | reverse %}

## Upcoming events

{% if future_events.size > 0 %}
{% for item in future_events limit:3 %}
<div class="event-item">
  {% assign thumb = nil %}
  {% if item.image %}
    {% assign thumb = item.image %}
  {% elsif item.thumbnail %}
    {% assign thumb = item.thumbnail %}
  {% elsif item.images and item.images.size > 0 %}
    {% assign thumb = item.images[0] %}
  {% endif %}

  {% if thumb %}
    <a href="{{ item.url | relative_url }}">
      <img src="{{ thumb | relative_url }}" alt="{{ item.title }}" />
    </a>
  {% endif %}

  <h3><a href="{{ item.url | relative_url }}">{{ item.title }}</a></h3>

  <p>
    {{ item.date | date: "%b %d, %Y at %H:%M" }}
    {% if item.enddate or item.end_date %} – {{ item.enddate | default: item.end_date | date: "%H:%M" }}{% endif %}
    {% if item.location %} — {{ item.location }}{% endif %}
  </p>

  {%- assign desc = item.description | default: item.excerpt -%}
  {%- if desc == nil or desc == "" -%}
    {%- assign desc = item.content | strip_html | truncatewords: 30 -%}
  {%- endif -%}
  {% if desc %}
    <p>{{ desc }}</p>
  {% endif %}
</div>
{% endfor %}
{% else %}
No upcoming events.
{% endif %}


## How?

MishMash will bring together a large multidisciplinary and cross-sectoral group of researchers and practitioners from the arts, humanities, social and natural sciences, design, and engineering. MishMash organises its theoretical and methodological "mishmash" into a structured "mesh," where projects and activities intersect across *themes*, *approaches*, and *perspectives*.

![MishMash Cube](/assets/images/cube/mishmash_cube.svg){: style="display:block;margin:0 auto;width:500px;" }

## Partners

---
<details>
    <summary>+ Norwegian research partners</summary>

    <ul>
        <li><a href="https://www.aho.no/english/">The Oslo School of Architecture and Design (AHO)</a></li>
        <li><a href="https://www.bi.edu/">Norwegian Business School (BI)</a></li>
        <li><a href="https://www.hiof.no/english/">Østfold University College (HiØ)</a></li>
        <li><a href="https://www.hvl.no/en/">Western Norway University of Applied Sciences (HVL)</a></li>
        <li><a href="https://www.inn.no/english/">University of Inland Norway (INN)</a></li>
        <li><a href="https://khio.no/en">The Oslo National Academy of the Arts (KHiO)</a></li>
        <li><a href="https://www.kristiania.no/en/">Kristiania University College (Kristiania)</a></li>
        <li><a href="https://www.nb.no/">National Library of Norway (In Norwegian)</a></li>
        <li><a href="https://nilu.com/">The Climate and Environmental Research Institute (NILU)</a></li>
        <li><a href="https://www.nla.no/en/">NLA University College (NLA)</a></li>
        <li><a href="https://nmh.no/en/">Norwegian Academy of Music (NMH)</a></li>
        <li><a href="https://www.nord.no/en">Nord University (Nord)</a></li>
        <li><a href="https://norsus.no/en/">Norwegian Institute for Sustainability Research (NORSUS)</a></li>
        <li><a href="https://www.ntnu.edu/">Norwegian University of Science and Technology (NTNU)</a></li>
        <li><a href="https://www.oslomet.no/en">Oslo Metropolitan University (OsloMet)</a></li>
        <li><a href="https://www.simulamet.no/">Simula Research Laboratory (SIMULAMET)</a></li>
        <li><a href="https://www.sintef.no/en/">The Foundation for Industrial and Technical Research (SINTEF)</a></li>
        <li><a href="https://www.uia.no/english/index.html">University of Agder (UiA)</a></li>
        <li><a href="https://www.uib.no/en">University of Bergen (UiB)</a></li>
        <li><a href="https://www.uio.no/english/index.html">University of Oslo (UiO)</a></li>
        <li><a href="https://en.uit.no/">University of Tromsø (UiT)</a></li>
    </ul>
</details>
---

<details>
    <summary>+ Other Norwegian partners</summary>
    <p>In alphabetical order:</p>
    <ul>
        <li><a href="https://akks.no/">AKKS Norge (In Norwegian)</a></li>
        <li><a href="https://annomuseum.no/en">ANNO</a></li>
        <li><a href="https://ateliernord.no/?lang=en">Atelier Nord</a></li>
        <li><a href="https://bek.no/en/">BEK</a></li>
        <li><a href="https://www.fib.no/en">Bergen International Festival</a></li>
        <li><a href="https://www.borealisfestival.no/en/home/">Borealis</a></li>
        <li><a href="https://www.cultiva.no/en/">Cultiva</a></li>
        <li><a href="https://dhko.no/en">DHKO</a></li>
        <li><a href="https://www.fyndreality.com/">Fynd Reality AS</a></li>
        <li><a href="https://www.gramart.no/">GramArt (In Norwegian)</a></li>
        <li><a href="https://en.gramo.no/">GRAMO</a></li>
        <li><a href="https://halogen.no/en/">Halogen AS</a></li>
        <li><a href="https://hamarregionen.no/move-to-the-hamar-region/">Hamarregionen utvikling</a></li>
        <li><a href="https://helseinn.no/">HelseINN (In Norwegian)</a></li>
        <li><a href="https://www.jmn.no/eng">JM Norway</a></li>
        <li><a href="https://kilden.com/en/">Kilden Performing Arts Centre</a></li>
        <li><a href="https://www.kodebergen.no/en">KODE Bergen Art Museum</a></li>
        <li><a href="https://www.kunstsilo.no/en">Kunstsilo</a></li>
        <li><a href="https://kulturskoleradet.no/">Kulturskolerådet (In Norwegian)</a></li>
        <li><a href="https://www.kulturtanken.no/">Kulturtanken (In Norwegian)</a></li>
        <li><a href="https://mediacitybergen.no/">Media Cluster Norway AS</a></li>
        <li>Multikjetil AS</li>
        <li><a href="https://www.nasjonalmuseet.no/en/">Nasjonalmuseet</a></li>
        <li><a href="https://kunstkultursenteret.no/english/">Norwegian Centre for Arts and Culture in Education (NCACE)</a></li>
        <li><a href="https://notam.no/en/">Notam</a></li>
        <li><a href="https://nopa.no/english/">Norwegian Society of Composers and Lyricists (NOPA)</a></li>
        <li><a href="https://www.naic.no/english/">Norwegian AI Cloud (NAIC)</a></li>
        <li><a href="https://www.nrk.no/">Norwegian Broadcasting Corporation (NRK) (In Norwegian)</a></li>
        <li><a href="https://www.kreativai.no/">Oslo Kreativ AI (OKAI)</a></li>
        <li><a href="https://polyfon.no/en_US/">Polyfon</a></li>
        <li><a href="https://punktfestival.no/">PUNKT</a></li>
        <li><a href="https://reimagine.no/">Reimagine AS</a></li>
        <li><a href="https://sareptastudio.com/">Sarepta Studio AS</a></li>
        <li><a href="https://skapia.no/">Skapia (In Norwegian)</a></li>
        <li><a href="https://innlandetfylke.no/">Skolene i Innlandet (In Norwegian)</a></li>
        <li><a href="https://www.storyphone.no/">StoryPhone AS (In Norwegian)</a></li>
        <li><a href="https://www.tekniskmuseum.no/en/">Oslo Science Centre</a></li>
        <li><a href="https://teks.no/">TEKS</a></li>
        <li><a href="https://www.tono.no/en/">TONO</a></li>
        <li><a href="https://www.ultima.no/en/">Ultima – Oslo Contemporary Music Festival</a></li>
        <li><a href="https://www.vestagdermuseet.no/">Vest‐Agder Museum</a></li>
        <li><a href="https://vrinn.no/">VRINN</a></li>
    </ul>
</details>
---

<details>
    <summary>+ International partners</summary>
Numerous international academic and non-academic partners will also be involved, and we will set up an affiliate program for others to join the network and participate in relevant activities. 
</details>
---


<div style="display:flex;justify-content:center;gap:24px;flex-wrap:nowrap;align-items:center;white-space:nowrap;">
    <img src="assets/images/logos/NFR/Sort/Stottet_av_Forskningsradet_logo_Engelsk_01_Weller_RGB.svg" alt="RCN logo" width="400">
    <a href="mailto:contact@mishmash.no" style="text-align:center;width:100px;display:inline-block;">
        <img src="/assets/images/icons/contact_email.svg" alt="Contact e-mail" width="64" style="display:block;margin:0 auto;">
        <span style="display:block;margin-top:8px;font-size:0.9rem;">Contact</span>
    </a>
    <a href="https://sympa.uio.no/mishmash.no/subscribe/announcements?previous_action=info" style="text-align:center;width:100px;display:inline-block;">
        <img src="/assets/images/icons/mailing_list.svg" alt="Mailing list" width="64" style="display:block;margin:0 auto;">
        <span style="display:block;margin-top:8px;font-size:0.9rem;">Mailing list</span>
    </a>
    <a href="https://www.linkedin.com/company/107529241/" style="text-align:center;width:100px;display:inline-block;">
        <img src="/assets/images/icons/linkedin.svg" alt="LinkedIn" width="64" style="display:block;margin:0 auto;">
        <span style="display:block;margin-top:8px;font-size:0.9rem;">LinkedIn</span>
    </a>
    <a href="https://www.instagram.com/aimishmash/" style="text-align:center;width:100px;display:inline-block;">
        <img src="/assets/images/icons/instagram.svg" alt="Instagram" width="64" style="display:block;margin:0 auto;">
        <span style="display:block;margin-top:8px;font-size:0.9rem;">Instagram</span>
    </a>
</div>
