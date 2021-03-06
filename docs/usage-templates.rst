.. _usage-templates:

Templates
=========

.. code-block:: django

   {% load flickr_tags %}

Small photo linking to flickr page

.. code-block:: django

   {% flickr_photo photo "small" 1 %}

Large photo without link

.. code-block:: django

   {% flickr_photo photo "large" %}



Photos
-------

.. code-block:: django
   :linenos:

   {% load flickr_tags %}

   <h1>Django-Flickr (Demo Page)</h1>

   <h2>Photos</h2>
	<ul class="flickr photos">
	{% for photo in photo_list %}
	<li>{% flickr_photo photo "small" 1 %}
		<h3><a href="{{ photo.get_absolute_url }}">{{ photo.title }}</a></h3>
		<p>{{ photo.description }}</p>
		<dl>
			<dt>taken</dt><dd>{{ photo.date_taken|date:"d.m.Y" }}</dd>
			<dt>tags</dt><dd>
				<ul class="tags">
					{% for tag in photo.tags.all %}
						<li>#{{ tag }}</li>
					{% endfor %}
					</ul>				
			</dd>
		</dl>
	</li>
	{% endfor %}
	</ul>
	{% include "flickr/pagination.html" %}
	

Photosets
----------

.. code-block:: django
   :linenos:

   {% load flickr_tags %}

   <h2>Photosets</h2>

	<ul class="flickr sets">
	{% for set in photosets %}
	{% if set.cover %}
	<li><a href="{{ set.get_absolute_url }}">{% flickr_photo set.cover "thumb" %}</a>
		<h3><a href="{{ set.get_absolute_url }}">{{ set.title }}</a></h3>		
	</li>
	{% endif %}
	{% endfor %}
	</ul>

Tags
-----

.. code-block:: django
   :linenos:
	
   {% load taggit_extras %}

   <h2>Tags</h2>
	
	{% get_taglist as tags for 'flickr' %}
	<ul class="tags">
	{% for tag in tags %}
		<li>#{{tag}} ({{tag.num_times}})</li>
	{% endfor %}
	</ul>
