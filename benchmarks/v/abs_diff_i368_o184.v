module abs_diff_i368_o184(a,b,r);
input [183:0] a,b;
output [183:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
