module abs_diff_i960_o480(a,b,r);
input [479:0] a,b;
output [479:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
