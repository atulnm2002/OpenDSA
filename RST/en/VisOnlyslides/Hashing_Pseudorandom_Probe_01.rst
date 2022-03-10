.. This file is part of the OpenDSA eTextbook project. See
.. http://opendsa.org for more details.
.. Copyright (c) 2012-2020 by the OpenDSA Project Contributors, and
.. distributed under an MIT open source license.

.. avmetadata::
   :author: Cliff Shaffer

.. slideconf::
   :autoslides: False


.. slide:: Pseudo-Random Probing

   .. inlineav:: collisionCON3 ss
      :long_name: Pseudo-Random Probing Slideshow
      :links: AV/Hashing/collisionCON.css
      :scripts: AV/Hashing/collisionCON3.js
      :output: show


.. slide:: Pseudo-Random Probing (2)

   .. inlineav:: collisionCON4 ss
      :long_name: Avoiding the Train
      :links: AV/Hashing/collisionCON.css
      :scripts: AV/Hashing/collisionCON4.js
      :output: show


.. slide:: Quadratic Probing

   .. inlineav:: collisionCON5 ss
      :long_name: Quadratic Probing Slideshow
      :links: AV/Hashing/collisionCON.css
      :scripts: AV/Hashing/collisionCON5.js
      :output: show

   .. inlineav:: collisionCON6 ss
      :long_name: Quadratic Probing Problem
      :links: AV/Hashing/collisionCON.css
      :scripts: AV/Hashing/collisionCON6.js
      :output: show


.. slide:: Double Hashing (1)

   .. inlineav:: collisionCON7 ss
      :long_name: Double Hashing Slideshow 2
      :links: AV/Hashing/collisionCON.css
      :scripts: AV/Hashing/collisionCON7.js
      :output: show


.. slide:: Double Hashing (2)

   .. inlineav:: collisionCON8 ss
      :long_name: Double Hashing Slideshow 3
      :links: AV/Hashing/collisionCON.css
      :scripts: AV/Hashing/collisionCON8.js
      :output: show


.. slide:: Analysis of Closed Hashing

   The load factor is :math:`\alpha = N/M` where :math:`N` is the
   number of records currently in the table.

   .. odsafig:: Images/hashplot.png
      :width: 600
      :align: center
      :capalign: justify
      :figwidth: 90%
      :alt: Hashing analysis plot


.. slide:: Deletion

   * Deleting a record must not hinder later searches.

   * We do not want to make positions in the hash table unusable because of
     deletion.

   * Both of these problems can be resolved by placing a special mark in
     place of the deleted record, called a tombstone.

   * A tombstone will not stop a search, but that slot can be used for
     future insertions.


.. slide:: Tombstones (1)

   .. inlineav:: hashdelCON ss
      :long_name: Hash Deletion Slideshow
      :links: 
      :scripts: AV/Hashing/hashdelCON.js
      :output: show


.. slide:: Tombstones (2)

   * Unfortunately, tombstones add to the average path length.

   * Solutions:
      #. Local reorganizations to try to shorten the average path length.
      #. Periodically rehash the table (by order of most frequently accessed
         record).
