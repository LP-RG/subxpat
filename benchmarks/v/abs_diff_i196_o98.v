module abs_diff_i196_o98(a,b,r);
input [97:0] a,b;
output [97:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
