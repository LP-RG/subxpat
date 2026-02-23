module abs_diff_i308_o154(a,b,r);
input [153:0] a,b;
output [153:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
