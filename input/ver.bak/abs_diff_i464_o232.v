module abs_diff_i464_o232(a,b,r);
input [231:0] a,b;
output [231:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
