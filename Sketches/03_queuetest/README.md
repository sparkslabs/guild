Dev notes:
Final version of this should have 3 actors.

* 1 should have be a recipient, that has an inbound queue.
  The 2 other actors add values to this inbound queue, without interfering
  with each other.  The recipient acts on this data.

* A second iteration of this should have 3 actors in a circle.

* Initially can actually just be 2 actors with one "pinging" the other, by
  placing data on it's inbound queue.

* The next stage would be the  2 actors with "pinging" each other, by
  placing data on the other's inbound queue.

We'll then be able to move onto the next stage.
