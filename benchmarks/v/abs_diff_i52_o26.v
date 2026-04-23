module abs_diff_i52_o26(a,b,r);
input [25:0] a,b;
output [25:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
