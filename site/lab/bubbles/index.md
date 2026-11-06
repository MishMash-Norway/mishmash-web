---
layout: lab
title: "MishMash Bubbles"
permalink: /lab/bubbles/
custom_css: /assets/css/bubbles.css
redirect_from:
  - /gallery/bubbles/
description: "The centre's emblem as a toy: solid balls with springy physics you can push around, add to, and retune."
lab:
  authors: [mishmash.no]
  date: 2026-02-01
  status: piece
  data: "None: the piece is the emblem's two circles, drawn as vectors and moved by a small physics loop in your browser."
  ai: "Coded with an AI assistant and reviewed by the site maintainers; see the AI colophon."
---

Move the pointer across the balls and they scatter, then pull themselves back. The controls below add more of them and change the seven numbers the motion is made of.

<div id="bubbles">
  <p>Loading the bubbles…</p>
</div>
<noscript><p>This piece needs JavaScript. The emblem it plays with is on every page of this site.</p></noscript>

<script defer src="{{ '/assets/js/bubbles.js' | relative_url }}"></script>

## What the controls do

Each slider sets one number in the loop, which is short enough to describe in full.

**Spring** pulls a ball back towards the place it started. Every frame, the distance from that resting place is multiplied by this number and added to the ball's speed. At zero the balls never come home and drift until something else stops them. Turned up, they snap back and overshoot, because the pull does not stop at the middle.

**Damping** is the fraction of speed a ball keeps from one frame to the next. At 1 nothing is ever lost and the balls ring forever. At 0.9 a shove dies within a second. This number does more than any other to set how stiff or sluggish the motion feels.

**Gravity** adds a constant downward push. Set it negative and the balls float up and rest against the ceiling instead.

**Pointer push** is how hard the pointer shoves a ball it passes through. The shove is strongest at the centre of the ball and fades to nothing at the edge of its reach, so a slow pass nudges and a fast one scatters.

**Wall bounce** is how much speed survives an edge. At 1 a ball leaves the wall as fast as it arrived; at 0 it stops dead against it.

**Ball bounce** is the same for a hit between two balls. At 1 they exchange their speeds almost completely, like billiard balls; at 0 they stop pushing at each other and slide apart.

**Size** is the radius of every ball. Bigger balls run out of room sooner, and with several of them on the stage the whole row starts pushing as one block.

## How the motion is made

There is no physics library here. Every frame, for every ball, four lines run in this order: add the spring pull to the speed, add gravity to the speed, multiply the speed by the damping, then add the speed to the position. That is Euler integration, the simplest way to turn a rule about how fast something moves into a position on screen. It is accurate enough for a toy, but a stiff spring makes the balls fly apart, as pushing the spring slider to its end shows.

## How two balls are kept apart

The balls are solid: two of them never share a space, and keeping that true is most of the work.

Every pair is measured. If the distance between two centres is less than two radii, they overlap, and each ball is moved back along the line between the centres by half the overlap. Then the part of their speed that lies along that same line is exchanged. That is an elastic collision written out by hand, and it is why a ball knocked into another passes its motion on instead of stopping.

Separating one pair can push a ball into a third, so the whole check runs twice per frame. Walls are handled after the balls, in the same two passes: a ball that has gone past an edge is put back on the edge, and its speed in that direction is reversed and scaled by the wall bounce. Handling balls first and walls last means a ball squeezed against the edge by another ends the frame inside the stage rather than outside it.

Two passes do not always resolve every overlap. With a dozen large balls crowded into a corner, two can still overlap for a frame before the next pass separates them. A physics engine would iterate until the whole arrangement is consistent; this one does a fixed amount of work per frame and accepts the occasional error, a trade-off every real-time simulation makes somewhere.

## What it costs

The number under the controls says how many pairs are being checked. It grows as the square of the ball count: two balls are one pair, twelve balls are sixty-six, and each pair is measured twice every frame. That is why the piece stops at twelve.

The loop stops when nothing is moving. Once every ball is within half a unit of its resting place and slower than a twentieth of a unit per frame, the piece waits half a second and then stops asking for frames, so an idle page in a background tab costs nothing until you touch it again.

A reader whose system asks for reduced motion gets the balls at rest, and they stay there until a control is used.

## Why this is here

The centre's emblem is two overlapping circles, and a logo is usually fixed. The piece makes it move to ask what the mark is for, and exposes the numbers so that the whole piece can be understood, which is not true of most of what a browser does.
