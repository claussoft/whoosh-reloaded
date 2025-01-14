import os.path
import random
import shutil
from datetime import datetime, timezone

from whoosh import fields, index, query
from whoosh.compat import text_type
from whoosh.util import now


def test_bigsort():
    times = 30000
    dirname = "testindex"

    df = fields.DATETIME(stored=True)
    schema = fields.Schema(id=fields.ID(stored=True), date=df)

    if os.path.exists(dirname):
        shutil.rmtree(dirname)
    os.mkdir(dirname)
    ix = index.create_in(dirname, schema)

    print("Writing...")
    t = now()
    w = ix.writer(limitmb=512)
    for i in range(times):
        dt = datetime.fromtimestamp(
            random.randint(15839593, 1294102139), tz=timezone.utc
        )
        w.add_document(id=text_type(i), date=dt)
    w.commit()
    print("Writing took ", now() - t)

    ix = index.open_dir(dirname)
    s = ix.searcher()
    q = query.Wildcard("id", "1?2*")

    t = now()
    x = list(df.sortable_terms(s.reader(), "date"))
    print(now() - t, len(x))

    t = now()
    for y in x:
        p = list(s.postings("date", y).all_ids())
    print(now() - t)

    t = now()
    r = s.search(q, limit=25, sortedby="date", reverse=True)
    print("Search 1 took", now() - t)
    print("len=", r.scored_length())

    t = now()
    r = s.search(q, limit=25, sortedby="date")
    print("Search 2 took", now() - t)

    t = now()
    r = s.search(q, limit=25, sortedby="date")
    print("Search 2 took", now() - t)

    from heapq import nlargest

    t = now()
    sf = s.stored_fields
    gen = ((sf(n)["date"], n) for n in q.docs(s))
    r = nlargest(25, gen)
    print(now() - t)
