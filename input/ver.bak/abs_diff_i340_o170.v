module abs_diff_i340_o170(a,b,r);
input [169:0] a,b;
output [169:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
