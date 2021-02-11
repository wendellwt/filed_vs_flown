#!/bin/bash -x

# new (Jan 29): publish to TWO different app_id's

if [ $# -ne 1 ] ; then
    echo "arg is either 'prod' which is app 194 or 'test' which is app 196"
    exit 1
fi

case "$1" in

  194|prod)

    # Published url (app_id=194) : http://172.26.21.40:3939/filed_vs_flown/
    #                            : http://172.26.21.40:3939/connect/#/apps/194

    APP_TITLE="filed_vs_flown"
    APP_ID=194
    rm -r rsconnect-python
    cp -r app_id_194_rsconnect-python rsconnect-python
    ;;

  196|test)

    # TESTING   url (app_id=196) : http://172.26.21.40:3939/content/196/
    #                            : http://172.26.21.40:3939/connect/#/apps/196

    APP_TITLE="test_filed_vs_flown"
    APP_ID=196
    rm -r rsconnect-python
    cp -r app_id_196_rsconnect-python rsconnect-python
    ;;

  *)
    echo $"Usage: $0 {prod|test|194|196}"
    exit 1
esac


# ======= fvf notes:

# problem 1: npm build put files in static dir, rs deploy (or flask) want them in
# the template dir
sed "s%cssi_star.png%/content/${APP_ID}/static/cssi_star.png%" static/index.html > templates/index.html

cp ../analysis/fvf_by_artcc.py copied/
cp ../analysis/everything.py copied/
cp ../analysis/get_feb.py copied/

STATIC_FILES=`find static/ -type f | grep -v index.html`

rsconnect deploy api --title $APP_TITLE --server http://172.26.21.40:3939 --api-key OV9jvi1YVE6WPYnSi09tX6i4UJvlciJc . \
     copied/fvf_by_artcc.py \
     copied/get_paths.py \
     copied/everything.py \
     copied/get_feb.py \
     templates/index.html  $STATIC_FILES

