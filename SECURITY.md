# Security

## Reporting a vulnerability

Report vulnerabilities privately through GitHub's private vulnerability
reporting for this repository (the **Security** tab, then **Report a
vulnerability**). Do not open a public issue or pull request for an
undisclosed vulnerability. Describe the affected command or file, the steps to
reproduce with fictional data, and the impact. Never include credentials,
private keys or account identifiers in a report.

Reports that matter most are anything that:

- accepts a package, delta, evaluation or release without a valid trusted
  signature, or with a key outside its trusted package and author;
- lets an expired or future-dated edition reach a live preview or an order;
- lets an edition reach a live preview or an order without paper permission
  for every key that signed it;
- makes the engine contact an endpoint other than Alpaca's paper endpoint;
- resends an order whose submission outcome is uncertain;
- lets data in a research package run code or fetch from the network.

## Reporting a compromised signing key

If you are an author and your private key may have been exposed:

1. Stop signing with it.
2. Generate a new key outside every Git checkout.
3. Open one pull request that:
   - changes the exposed key's `status` to `revoked` in `catalog/authors.json`
     and appends the new key, with today's date as its `valid_from`. A status
     change is the only edit the append-only rule allows, so nothing is
     deleted;
   - replaces each of your edition directories under `history/` with a copy
     re-signed with the new key, written by
     `public-pilot resign-edition DIR NEW_DIR --key FILE --key-id ID`. The
     copy's snapshot, evaluation and release carry new signatures; its
     payloads, `REPORT.md` and `account.fixture.json` are unchanged, so every
     hash and `history/INDEX.md` stay the same;
   - deletes, instead of re-signing, the directory of any edition that was
     forged with the exposed key, and says so. Only an edition whose
     signatures are all by revoked keys may be deleted.

   If you cannot open the pull request yourself, report it through private
   vulnerability reporting and the maintainers will.
4. Sign your current edition again with the new key: the same payload, with
   `public-pilot sign snapshot`. Give it to your readers. Editions that you
   published before the change and add to `history/` later are signed with
   the new key too.

Step 9 of the walkthrough in [docs/AUTHORING.md](docs/AUTHORING.md) runs this
procedure on a fictional edition. `public-pilot catalog check` accepts an
edition signed with the new key because you already had a key for the product
when the edition was published; editions signed only by a revoked key fail
the check. For every pull request, continuous integration also runs the base
branch's catalog check on the pull request's files, without running the pull
request's code: an existing edition must keep its payloads, report and
fixture, and only an edition signed entirely with revoked keys may disappear.

Maintainers confirm every revocation with the key's author through a second
channel before merging it, because a revocation lets that author's editions be
deleted.

A key that is only being replaced, not exposed, should be set to `retired`.
Retired keys still verify past editions, and `public-pilot catalog trust`
never grants them paper trading.

If you read or license research:

1. Remove the revoked key from your local trust file, or write a new file with
   `public-pilot catalog trust`, which leaves revoked keys out. From then on,
   `show`, `preview` and `execute-paper` refuse an installed edition whose
   proof chain needs the removed key; `cancel-paper` still works.
2. Install a full snapshot signed with a key you trust, into your existing
   state directory: the author's re-signed copy of the edition you have, or a
   newer edition. It replaces the installed edition although that edition's
   key is no longer trusted, and your plans and order records stay. The
   engine compares it with the edition as it was verified when you installed
   it, and still refuses an older edition, a cutoff that moves backwards,
   another author or purpose, and different content under an edition ID you
   installed. A delta cannot build on an edition whose key you removed;
   install the full snapshot.
3. Preview a new plan. A plan made from different research cannot place
   orders; one made from the same edition, now re-signed, still can.

If the edition you installed may itself have been forged with the exposed key,
its dates can block the genuine replacement. Then cancel any outstanding
execution with `cancel-paper`, keep that state directory as the record of your
orders, and install the genuine edition into a new state directory.

## Scope

The engine trades only in Alpaca paper accounts. Never test with live-trading
credentials.
