module abs_diff_i912_o456(a,b,r);
input [455:0] a,b;
output [455:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
