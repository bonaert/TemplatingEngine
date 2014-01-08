from collections import deque
import re
from Exception import TemplateSyntaxException
from Constants import *

ROOT = 'root'

# bind operators to token types
operators = {
    '+': TOKEN_ADD,
    '-': TOKEN_SUB,
    '/': TOKEN_DIV,
    '//': TOKEN_FLOORDIV,
    '*': TOKEN_MUL,
    '%': TOKEN_MOD,
    '**': TOKEN_POW,
    '~': TOKEN_TILDE,
    '[': TOKEN_LBRACKET,
    ']': TOKEN_RBRACKET,
    '(': TOKEN_LPAREN,
    ')': TOKEN_RPAREN,
    '{': TOKEN_LBRACE,
    '}': TOKEN_RBRACE,
    '==': TOKEN_EQ,
    '!=': TOKEN_NE,
    '>': TOKEN_GT,
    '>=': TOKEN_GTEQ,
    '<': TOKEN_LT,
    '<=': TOKEN_LTEQ,
    '=': TOKEN_ASSIGN,
    '.': TOKEN_DOT,
    ':': TOKEN_COLON,
    '|': TOKEN_PIPE,
    ',': TOKEN_COMMA,
    ';': TOKEN_SEMICOLON
}

# static regular expressions
newline_re = re.compile(r'(\r\n|\r|\n)')
whitespace_re = re.compile(r'\s+', re.U)
float_re = re.compile(r'(?<!\.)\d+\.\d+')
integer_re = re.compile(r'\d+')
name_start = '\u0041-\u005A\u005F\u0061-\u007A\u00AA\u00B5\u00BA\u00C0-\u00D6\u00D8-\u00F6\u00F8-\u01BA\u01BB\u01BC-\u01BF\u01C0-\u01C3\u01C4-\u0241\u0250-\u02AF\u02B0-\u02C1\u02C6-\u02D1\u02E0-\u02E4\u02EE\u0386\u0388-\u038A\u038C\u038E-\u03A1\u03A3-\u03CE\u03D0-\u03F5\u03F7-\u0481\u048A-\u04CE\u04D0-\u04F9\u0500-\u050F\u0531-\u0556\u0559\u0561-\u0587\u05D0-\u05EA\u05F0-\u05F2\u0621-\u063A\u0640\u0641-\u064A\u066E-\u066F\u0671-\u06D3\u06D5\u06E5-\u06E6\u06EE-\u06EF\u06FA-\u06FC\u06FF\u0710\u0712-\u072F\u074D-\u076D\u0780-\u07A5\u07B1\u0904-\u0939\u093D\u0950\u0958-\u0961\u097D\u0985-\u098C\u098F-\u0990\u0993-\u09A8\u09AA-\u09B0\u09B2\u09B6-\u09B9\u09BD\u09CE\u09DC-\u09DD\u09DF-\u09E1\u09F0-\u09F1\u0A05-\u0A0A\u0A0F-\u0A10\u0A13-\u0A28\u0A2A-\u0A30\u0A32-\u0A33\u0A35-\u0A36\u0A38-\u0A39\u0A59-\u0A5C\u0A5E\u0A72-\u0A74\u0A85-\u0A8D\u0A8F-\u0A91\u0A93-\u0AA8\u0AAA-\u0AB0\u0AB2-\u0AB3\u0AB5-\u0AB9\u0ABD\u0AD0\u0AE0-\u0AE1\u0B05-\u0B0C\u0B0F-\u0B10\u0B13-\u0B28\u0B2A-\u0B30\u0B32-\u0B33\u0B35-\u0B39\u0B3D\u0B5C-\u0B5D\u0B5F-\u0B61\u0B71\u0B83\u0B85-\u0B8A\u0B8E-\u0B90\u0B92-\u0B95\u0B99-\u0B9A\u0B9C\u0B9E-\u0B9F\u0BA3-\u0BA4\u0BA8-\u0BAA\u0BAE-\u0BB9\u0C05-\u0C0C\u0C0E-\u0C10\u0C12-\u0C28\u0C2A-\u0C33\u0C35-\u0C39\u0C60-\u0C61\u0C85-\u0C8C\u0C8E-\u0C90\u0C92-\u0CA8\u0CAA-\u0CB3\u0CB5-\u0CB9\u0CBD\u0CDE\u0CE0-\u0CE1\u0D05-\u0D0C\u0D0E-\u0D10\u0D12-\u0D28\u0D2A-\u0D39\u0D60-\u0D61\u0D85-\u0D96\u0D9A-\u0DB1\u0DB3-\u0DBB\u0DBD\u0DC0-\u0DC6\u0E01-\u0E30\u0E32\u0E40-\u0E45\u0E46\u0E81-\u0E82\u0E84\u0E87-\u0E88\u0E8A\u0E8D\u0E94-\u0E97\u0E99-\u0E9F\u0EA1-\u0EA3\u0EA5\u0EA7\u0EAA-\u0EAB\u0EAD-\u0EB0\u0EB2\u0EBD\u0EC0-\u0EC4\u0EC6\u0EDC-\u0EDD\u0F00\u0F40-\u0F47\u0F49-\u0F6A\u0F88-\u0F8B\u1000-\u1021\u1023-\u1027\u1029-\u102A\u1050-\u1055\u10A0-\u10C5\u10D0-\u10FA\u10FC\u1100-\u1159\u115F-\u11A2\u11A8-\u11F9\u1200-\u1248\u124A-\u124D\u1250-\u1256\u1258\u125A-\u125D\u1260-\u1288\u128A-\u128D\u1290-\u12B0\u12B2-\u12B5\u12B8-\u12BE\u12C0\u12C2-\u12C5\u12C8-\u12D6\u12D8-\u1310\u1312-\u1315\u1318-\u135A\u1380-\u138F\u13A0-\u13F4\u1401-\u166C\u166F-\u1676\u1681-\u169A\u16A0-\u16EA\u16EE-\u16F0\u1700-\u170C\u170E-\u1711\u1720-\u1731\u1740-\u1751\u1760-\u176C\u176E-\u1770\u1780-\u17B3\u17D7\u17DC\u1820-\u1842\u1843\u1844-\u1877\u1880-\u18A8\u1900-\u191C\u1950-\u196D\u1970-\u1974\u1980-\u19A9\u19C1-\u19C7\u1A00-\u1A16\u1D00-\u1D2B\u1D2C-\u1D61\u1D62-\u1D77\u1D78\u1D79-\u1D9A\u1D9B-\u1DBF\u1E00-\u1E9B\u1EA0-\u1EF9\u1F00-\u1F15\u1F18-\u1F1D\u1F20-\u1F45\u1F48-\u1F4D\u1F50-\u1F57\u1F59\u1F5B\u1F5D\u1F5F-\u1F7D\u1F80-\u1FB4\u1FB6-\u1FBC\u1FBE\u1FC2-\u1FC4\u1FC6-\u1FCC\u1FD0-\u1FD3\u1FD6-\u1FDB\u1FE0-\u1FEC\u1FF2-\u1FF4\u1FF6-\u1FFC\u2071\u207F\u2090-\u2094\u2102\u2107\u210A-\u2113\u2115\u2118\u2119-\u211D\u2124\u2126\u2128\u212A-\u212D\u212E\u212F-\u2131\u2133-\u2134\u2135-\u2138\u2139\u213C-\u213F\u2145-\u2149\u2160-\u2183\u2C00-\u2C2E\u2C30-\u2C5E\u2C80-\u2CE4\u2D00-\u2D25\u2D30-\u2D65\u2D6F\u2D80-\u2D96\u2DA0-\u2DA6\u2DA8-\u2DAE\u2DB0-\u2DB6\u2DB8-\u2DBE\u2DC0-\u2DC6\u2DC8-\u2DCE\u2DD0-\u2DD6\u2DD8-\u2DDE\u3005\u3006\u3007\u3021-\u3029\u3031-\u3035\u3038-\u303A\u303B\u303C\u3041-\u3096\u309D-\u309E\u309F\u30A1-\u30FA\u30FC-\u30FE\u30FF\u3105-\u312C\u3131-\u318E\u31A0-\u31B7\u31F0-\u31FF\u3400-\u4DB5\u4E00-\u9FBB\uA000-\uA014\uA015\uA016-\uA48C\uA800-\uA801\uA803-\uA805\uA807-\uA80A\uA80C-\uA822\uAC00-\uD7A3\uF900-\uFA2D\uFA30-\uFA6A\uFA70-\uFAD9\uFB00-\uFB06\uFB13-\uFB17\uFB1D\uFB1F-\uFB28\uFB2A-\uFB36\uFB38-\uFB3C\uFB3E\uFB40-\uFB41\uFB43-\uFB44\uFB46-\uFBB1\uFBD3-\uFC5D\uFC64-\uFD3D\uFD50-\uFD8F\uFD92-\uFDC7\uFDF0-\uFDF9\uFE71\uFE73\uFE77\uFE79\uFE7B\uFE7D\uFE7F-\uFEFC\uFF21-\uFF3A\uFF41-\uFF5A\uFF66-\uFF6F\uFF70\uFF71-\uFF9D\uFFA0-\uFFBE\uFFC2-\uFFC7\uFFCA-\uFFCF\uFFD2-\uFFD7\uFFDA-\uFFDC'
name_continue = '\u0030-\u0039\u0041-\u005A\u005F\u0061-\u007A\u00AA\u00B5\u00B7\u00BA\u00C0-\u00D6\u00D8-\u00F6\u00F8-\u01BA\u01BB\u01BC-\u01BF\u01C0-\u01C3\u01C4-\u0241\u0250-\u02AF\u02B0-\u02C1\u02C6-\u02D1\u02E0-\u02E4\u02EE\u0300-\u036F\u0386\u0388-\u038A\u038C\u038E-\u03A1\u03A3-\u03CE\u03D0-\u03F5\u03F7-\u0481\u0483-\u0486\u048A-\u04CE\u04D0-\u04F9\u0500-\u050F\u0531-\u0556\u0559\u0561-\u0587\u0591-\u05B9\u05BB-\u05BD\u05BF\u05C1-\u05C2\u05C4-\u05C5\u05C7\u05D0-\u05EA\u05F0-\u05F2\u0610-\u0615\u0621-\u063A\u0640\u0641-\u064A\u064B-\u065E\u0660-\u0669\u066E-\u066F\u0670\u0671-\u06D3\u06D5\u06D6-\u06DC\u06DF-\u06E4\u06E5-\u06E6\u06E7-\u06E8\u06EA-\u06ED\u06EE-\u06EF\u06F0-\u06F9\u06FA-\u06FC\u06FF\u0710\u0711\u0712-\u072F\u0730-\u074A\u074D-\u076D\u0780-\u07A5\u07A6-\u07B0\u07B1\u0901-\u0902\u0903\u0904-\u0939\u093C\u093D\u093E-\u0940\u0941-\u0948\u0949-\u094C\u094D\u0950\u0951-\u0954\u0958-\u0961\u0962-\u0963\u0966-\u096F\u097D\u0981\u0982-\u0983\u0985-\u098C\u098F-\u0990\u0993-\u09A8\u09AA-\u09B0\u09B2\u09B6-\u09B9\u09BC\u09BD\u09BE-\u09C0\u09C1-\u09C4\u09C7-\u09C8\u09CB-\u09CC\u09CD\u09CE\u09D7\u09DC-\u09DD\u09DF-\u09E1\u09E2-\u09E3\u09E6-\u09EF\u09F0-\u09F1\u0A01-\u0A02\u0A03\u0A05-\u0A0A\u0A0F-\u0A10\u0A13-\u0A28\u0A2A-\u0A30\u0A32-\u0A33\u0A35-\u0A36\u0A38-\u0A39\u0A3C\u0A3E-\u0A40\u0A41-\u0A42\u0A47-\u0A48\u0A4B-\u0A4D\u0A59-\u0A5C\u0A5E\u0A66-\u0A6F\u0A70-\u0A71\u0A72-\u0A74\u0A81-\u0A82\u0A83\u0A85-\u0A8D\u0A8F-\u0A91\u0A93-\u0AA8\u0AAA-\u0AB0\u0AB2-\u0AB3\u0AB5-\u0AB9\u0ABC\u0ABD\u0ABE-\u0AC0\u0AC1-\u0AC5\u0AC7-\u0AC8\u0AC9\u0ACB-\u0ACC\u0ACD\u0AD0\u0AE0-\u0AE1\u0AE2-\u0AE3\u0AE6-\u0AEF\u0B01\u0B02-\u0B03\u0B05-\u0B0C\u0B0F-\u0B10\u0B13-\u0B28\u0B2A-\u0B30\u0B32-\u0B33\u0B35-\u0B39\u0B3C\u0B3D\u0B3E\u0B3F\u0B40\u0B41-\u0B43\u0B47-\u0B48\u0B4B-\u0B4C\u0B4D\u0B56\u0B57\u0B5C-\u0B5D\u0B5F-\u0B61\u0B66-\u0B6F\u0B71\u0B82\u0B83\u0B85-\u0B8A\u0B8E-\u0B90\u0B92-\u0B95\u0B99-\u0B9A\u0B9C\u0B9E-\u0B9F\u0BA3-\u0BA4\u0BA8-\u0BAA\u0BAE-\u0BB9\u0BBE-\u0BBF\u0BC0\u0BC1-\u0BC2\u0BC6-\u0BC8\u0BCA-\u0BCC\u0BCD\u0BD7\u0BE6-\u0BEF\u0C01-\u0C03\u0C05-\u0C0C\u0C0E-\u0C10\u0C12-\u0C28\u0C2A-\u0C33\u0C35-\u0C39\u0C3E-\u0C40\u0C41-\u0C44\u0C46-\u0C48\u0C4A-\u0C4D\u0C55-\u0C56\u0C60-\u0C61\u0C66-\u0C6F\u0C82-\u0C83\u0C85-\u0C8C\u0C8E-\u0C90\u0C92-\u0CA8\u0CAA-\u0CB3\u0CB5-\u0CB9\u0CBC\u0CBD\u0CBE\u0CBF\u0CC0-\u0CC4\u0CC6\u0CC7-\u0CC8\u0CCA-\u0CCB\u0CCC-\u0CCD\u0CD5-\u0CD6\u0CDE\u0CE0-\u0CE1\u0CE6-\u0CEF\u0D02-\u0D03\u0D05-\u0D0C\u0D0E-\u0D10\u0D12-\u0D28\u0D2A-\u0D39\u0D3E-\u0D40\u0D41-\u0D43\u0D46-\u0D48\u0D4A-\u0D4C\u0D4D\u0D57\u0D60-\u0D61\u0D66-\u0D6F\u0D82-\u0D83\u0D85-\u0D96\u0D9A-\u0DB1\u0DB3-\u0DBB\u0DBD\u0DC0-\u0DC6\u0DCA\u0DCF-\u0DD1\u0DD2-\u0DD4\u0DD6\u0DD8-\u0DDF\u0DF2-\u0DF3\u0E01-\u0E30\u0E31\u0E32-\u0E33\u0E34-\u0E3A\u0E40-\u0E45\u0E46\u0E47-\u0E4E\u0E50-\u0E59\u0E81-\u0E82\u0E84\u0E87-\u0E88\u0E8A\u0E8D\u0E94-\u0E97\u0E99-\u0E9F\u0EA1-\u0EA3\u0EA5\u0EA7\u0EAA-\u0EAB\u0EAD-\u0EB0\u0EB1\u0EB2-\u0EB3\u0EB4-\u0EB9\u0EBB-\u0EBC\u0EBD\u0EC0-\u0EC4\u0EC6\u0EC8-\u0ECD\u0ED0-\u0ED9\u0EDC-\u0EDD\u0F00\u0F18-\u0F19\u0F20-\u0F29\u0F35\u0F37\u0F39\u0F3E-\u0F3F\u0F40-\u0F47\u0F49-\u0F6A\u0F71-\u0F7E\u0F7F\u0F80-\u0F84\u0F86-\u0F87\u0F88-\u0F8B\u0F90-\u0F97\u0F99-\u0FBC\u0FC6\u1000-\u1021\u1023-\u1027\u1029-\u102A\u102C\u102D-\u1030\u1031\u1032\u1036-\u1037\u1038\u1039\u1040-\u1049\u1050-\u1055\u1056-\u1057\u1058-\u1059\u10A0-\u10C5\u10D0-\u10FA\u10FC\u1100-\u1159\u115F-\u11A2\u11A8-\u11F9\u1200-\u1248\u124A-\u124D\u1250-\u1256\u1258\u125A-\u125D\u1260-\u1288\u128A-\u128D\u1290-\u12B0\u12B2-\u12B5\u12B8-\u12BE\u12C0\u12C2-\u12C5\u12C8-\u12D6\u12D8-\u1310\u1312-\u1315\u1318-\u135A\u135F\u1369-\u1371\u1380-\u138F\u13A0-\u13F4\u1401-\u166C\u166F-\u1676\u1681-\u169A\u16A0-\u16EA\u16EE-\u16F0\u1700-\u170C\u170E-\u1711\u1712-\u1714\u1720-\u1731\u1732-\u1734\u1740-\u1751\u1752-\u1753\u1760-\u176C\u176E-\u1770\u1772-\u1773\u1780-\u17B3\u17B6\u17B7-\u17BD\u17BE-\u17C5\u17C6\u17C7-\u17C8\u17C9-\u17D3\u17D7\u17DC\u17DD\u17E0-\u17E9\u180B-\u180D\u1810-\u1819\u1820-\u1842\u1843\u1844-\u1877\u1880-\u18A8\u18A9\u1900-\u191C\u1920-\u1922\u1923-\u1926\u1927-\u1928\u1929-\u192B\u1930-\u1931\u1932\u1933-\u1938\u1939-\u193B\u1946-\u194F\u1950-\u196D\u1970-\u1974\u1980-\u19A9\u19B0-\u19C0\u19C1-\u19C7\u19C8-\u19C9\u19D0-\u19D9\u1A00-\u1A16\u1A17-\u1A18\u1A19-\u1A1B\u1D00-\u1D2B\u1D2C-\u1D61\u1D62-\u1D77\u1D78\u1D79-\u1D9A\u1D9B-\u1DBF\u1DC0-\u1DC3\u1E00-\u1E9B\u1EA0-\u1EF9\u1F00-\u1F15\u1F18-\u1F1D\u1F20-\u1F45\u1F48-\u1F4D\u1F50-\u1F57\u1F59\u1F5B\u1F5D\u1F5F-\u1F7D\u1F80-\u1FB4\u1FB6-\u1FBC\u1FBE\u1FC2-\u1FC4\u1FC6-\u1FCC\u1FD0-\u1FD3\u1FD6-\u1FDB\u1FE0-\u1FEC\u1FF2-\u1FF4\u1FF6-\u1FFC\u203F-\u2040\u2054\u2071\u207F\u2090-\u2094\u20D0-\u20DC\u20E1\u20E5-\u20EB\u2102\u2107\u210A-\u2113\u2115\u2118\u2119-\u211D\u2124\u2126\u2128\u212A-\u212D\u212E\u212F-\u2131\u2133-\u2134\u2135-\u2138\u2139\u213C-\u213F\u2145-\u2149\u2160-\u2183\u2C00-\u2C2E\u2C30-\u2C5E\u2C80-\u2CE4\u2D00-\u2D25\u2D30-\u2D65\u2D6F\u2D80-\u2D96\u2DA0-\u2DA6\u2DA8-\u2DAE\u2DB0-\u2DB6\u2DB8-\u2DBE\u2DC0-\u2DC6\u2DC8-\u2DCE\u2DD0-\u2DD6\u2DD8-\u2DDE\u3005\u3006\u3007\u3021-\u3029\u302A-\u302F\u3031-\u3035\u3038-\u303A\u303B\u303C\u3041-\u3096\u3099-\u309A\u309D-\u309E\u309F\u30A1-\u30FA\u30FC-\u30FE\u30FF\u3105-\u312C\u3131-\u318E\u31A0-\u31B7\u31F0-\u31FF\u3400-\u4DB5\u4E00-\u9FBB\uA000-\uA014\uA015\uA016-\uA48C\uA800-\uA801\uA802\uA803-\uA805\uA806\uA807-\uA80A\uA80B\uA80C-\uA822\uA823-\uA824\uA825-\uA826\uA827\uAC00-\uD7A3\uF900-\uFA2D\uFA30-\uFA6A\uFA70-\uFAD9\uFB00-\uFB06\uFB13-\uFB17\uFB1D\uFB1E\uFB1F-\uFB28\uFB2A-\uFB36\uFB38-\uFB3C\uFB3E\uFB40-\uFB41\uFB43-\uFB44\uFB46-\uFBB1\uFBD3-\uFC5D\uFC64-\uFD3D\uFD50-\uFD8F\uFD92-\uFDC7\uFDF0-\uFDF9\uFE00-\uFE0F\uFE20-\uFE23\uFE33-\uFE34\uFE4D-\uFE4F\uFE71\uFE73\uFE77\uFE79\uFE7B\uFE7D\uFE7F-\uFEFC\uFF10-\uFF19\uFF21-\uFF3A\uFF3F\uFF41-\uFF5A\uFF66-\uFF6F\uFF70\uFF71-\uFF9D\uFF9E-\uFF9F\uFFA0-\uFFBE\uFFC2-\uFFC7\uFFCA-\uFFCF\uFFD2-\uFFD7\uFFDA-\uFFDC'
name_re = re.compile(r'\b[%s][%s]*\b' % (name_start, name_continue))
string_re = re.compile(r"('([^'\\]*(?:\\.[^'\\]*)*)'"
                       r'|"([^"\\]*(?:\\.[^"\\]*)*)")', re.S)
operator_re = re.compile('(%s)' % '|'.join(re.escape(x) for x in
                                           sorted(operators, key=lambda x: -len(x))))


class Rule():
    def __init__(self, pattern, tokens_type, new_state):
        self._pattern = pattern
        self._tokens_type = tokens_type
        self._new_state = new_state
        self._regex = re.compile(pattern)

    def match(self, text):
        return self._regex.match(text)

    def items(self):
        return self._regex, self._tokens_type, self._new_state


class Token():
    def __init__(self, token_type, value):
        self.token_type = token_type
        self.value = value

    def test(self, expr):
        if self.token_type == expr:
            return True
        elif ':' in expr:
            return expr.split(':') == [self.token_type, self.value]
        else:
            return False

    def items(self):
        return (self.token_type, self.value)

    def test_any(self, *iterable):
        return any(self.test(expr) for expr in iterable)

    def __repr__(self):
        return "Token(type: %s, value: %s)" % (self.token_type, self.value)


class TokenStreamIterator(object):
    def __init__(self, token_stream):
        self.stream = token_stream

    def __iter__(self):
        return self

    def __next__(self):
        token = self.stream.current
        if token.token_type == TOKEN_EOF:
            self.stream.close()
            raise StopIteration()
        next(self.stream)
        return token


class TokenStream():
    def __init__(self, generator):
        self._iter = iter(generator)
        self.current = Token(TOKEN_INITIAL, '')
        # Used for look()
        self._pushed = deque()
        next(self)

    def __iter__(self):
        return TokenStreamIterator(self)

    def __bool__(self):
        return self.current.token_type is not TOKEN_EOF

    def has_ended(self):
        return self.current.token_type is TOKEN_EOF

    def push(self, token):
        self._pushed.append(token)

    def look(self):
        token = next(self)
        new_token = self.current
        self.push(new_token)
        self.current = token
        return new_token

    def expect(self, expr):
        if not self.current.test(expr):
            if self.current.token_type == TOKEN_EOF:
                raise TemplateSyntaxException('Reached unexpected end of file')
            else:
                raise TemplateSyntaxException('Expected %s but got %s' % (expr, self.current))
        try:
            return self.current
        finally:
            next(self)

    def skip(self, n=1):
        for _ in range(n):
            next(self)

    def next_if(self, expr):
        if self.current.test(expr):
            return next(self)

    def skip_if(self, expr):
        return self.next_if(expr) is not None

    def __next__(self):
        old = self.current
        if self._pushed:
            self.current = self._pushed.popleft()
        elif self.current.token_type is not TOKEN_EOF:
            try:
                self.current = next(self._iter)
            except StopIteration:
                self.close()
        return old

    def close(self):
        self.current = Token(TOKEN_EOF, '')
        self._iter = None


class Lexer():
    def __init__(self):
        self.tag_rules = [
            Rule(whitespace_re, TOKEN_WHITESPACE, None),
            Rule(float_re, TOKEN_FLOAT, None),
            Rule(integer_re, TOKEN_INTEGER, None),
            Rule(name_re, TOKEN_NAME, None),
            Rule(string_re, TOKEN_STRING, None),
            Rule(operator_re, TOKEN_OPERATOR, None)
        ]
        self.rules = self.compile_rules()
        self.line_number = 0
        self.position = 0
        self.current_match_result = None
        self.current_regex = None
        self.node_stack = []
        self.current_rules = None

    def compile_rules(self):
        return {ROOT: self.compile_root_rules(),
                TOKEN_BLOCK_START: self.compile_block_start_rules(),
                TOKEN_VARIABLE_START: self.compile_variable_start_rules()}

    def compile_root_rules(self):
        return [self.compile_block_rule(),
                self.compile_data_rule()]

    def compile_block_start_rules(self):
        pattern = BLOCK_END_STRING
        return [Rule(pattern, TOKEN_BLOCK_END, '#pop')] + self.tag_rules

    def compile_variable_start_rules(self):
        pattern = VARIABLE_END_STRING
        return [Rule(pattern, TOKEN_VARIABLE_END, '#pop')] + self.tag_rules

    def compile_block_rule(self):
        rules = [
            (len(BLOCK_START_STRING), 'block', BLOCK_START_STRING),
            (len(VARIABLE_START_STRING), 'variable', VARIABLE_START_STRING)
        ]

        # sorts rule by length => raw text will be last option (bit of a hack)
        rules = (x[1:] for x in sorted(rules, reverse=True))
        regexes = self.build_regex_patterns(rules)
        final_pattern = '(.*?)(?:%s)' % '|'.join(regexes)
        return Rule(final_pattern, (TOKEN_DATA, '#bygroup'), '#bygroup')

    def compile_data_rule(self):
        return Rule('.+', TOKEN_DATA, None)

    def build_regex_pattern(self, group_name, rule):
        return r'(?P<%s_start>%s)' % (group_name, rule)

    def build_regex_patterns(self, rules):
        return (self.build_regex_pattern(group, rule) for group, rule in rules)

    def tokenize(self, source):
        stream = self.tokenize_source(source)
        tokens = self.make_tokens(stream)
        return TokenStream(tokens)

    def make_tokens(self, stream):
        for token_type, value in stream:
            if token_type == TOKEN_WHITESPACE:
                continue
            elif token_type == TOKEN_INTEGER:
                value = int(value)
            elif token_type == TOKEN_FLOAT:
                value = float(value)
            elif token_type == TOKEN_NAME:
                value = str(value)
            elif token_type == TOKEN_STRING:
                value = str(value[1:-1])
            elif token_type == TOKEN_OPERATOR:
                token_type = operators[value]
            yield Token(token_type, value)

    def tokenize_source(self, source):
        source_length = len(source)
        self.node_stack = ['root']
        self.current_rules = self.rules[self.node_stack[-1]]
        while True:
            for regex, token_types, new_state in self.rules_items():
                self.current_match_result = regex.match(source, self.position)

                if self.current_match_result is None:
                    continue
                else:
                    results = self.process_match(token_types)
                    if isinstance(results, list):
                        for result in results:
                            yield result
                    else:
                        yield results

                    self.update_state(new_state)
                    self.update_position()
                    break
            else:
                if self.position == source_length:
                    return
                raise TemplateSyntaxException('Unexpected char %r at position %d' %
                                              (source[self.position], self.position))

    def rules_items(self):
        for rule in self.current_rules:
            yield rule.items()

    def process_match(self, possible_token_types):
        if isinstance(possible_token_types, tuple):
            return self.process_result_from_group(possible_token_types)
        else:
            return possible_token_types, self.current_match_result.group()

    def process_result_from_group(self, possible_token_types):
        result = []

        for (index, possible_token_type) in enumerate(possible_token_types):
            if possible_token_type == '#bygroup':
                return result + [self.process_result_from_by_group()]
            else:
                value = self.process_result_from_normal_group(possible_token_type, index)
                if value:
                    result.append(value)

        return result

    def process_result_from_by_group(self):
        for group_token_type, token_text in self.current_match_result.groupdict().items():
            if token_text is not None:
                return group_token_type, token_text

    def process_result_from_normal_group(self, possible_token_type, index):
        data = self.current_match_result.group(index + 1)
        if data:
            return possible_token_type, data
        self.line_number += data.count('\n')

    def update_state(self, new_state):
        if new_state is not None:
            self.change_state(new_state)
            self.update_rules()

    def change_state(self, new_state):
        if new_state == '#pop':
            self.node_stack.pop()
        elif new_state == '#bygroup':
            self.add_appropriate_group_type_to_stack()
        else:
            self.node_stack.append(new_state)

    def add_appropriate_group_type_to_stack(self):
        for group_type, text in self.current_match_result.groupdict().items():
            if text is not None:
                self.node_stack.append(group_type)
                return

    def update_position(self):
        new_position = self.current_match_result.end()
        if self.position == new_position:
            raise TemplateSyntaxException(
                '%s yielded empty string without stack change' % self.current_match_result.group())
        self.position = new_position

    def update_rules(self):
        self.current_rules = self.rules[self.node_stack[-1]]
