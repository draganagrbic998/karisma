def email_html(data):
    # ['Country', 'Hotel', 'Count In', 'Count Out', 'Room', 'Pax', 'Available', 'Rate']

    result = {}
    for row in data:
        title = '{}, {} ({} - {})'.format(row[1], row[0], row[2].replace('-', '/'), row[3].replace('-', '/'))
        if title not in result:
            result[title] = []
        result[title].append(row)

    html = ''
    for title in result:
        html += '<h3>{}</h3><ol>'.format(title)
        for row in result[title]:
            html += """
                <li>
                    <div>{}</div>
                    {}
                    <div>{}</div>
                </li>
            """.format(row[4], '<div>{}</div>'.format(row[5]) if row[5] else '', '<b>{}$</b>, <i>Available</i>'.format(row[7]) if row[7] else '<b>Not Available</b>')
        html += '</ol>'
    return html

