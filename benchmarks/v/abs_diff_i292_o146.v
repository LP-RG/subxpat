module abs_diff_i292_o146(a,b,r);
input [145:0] a,b;
output [145:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
