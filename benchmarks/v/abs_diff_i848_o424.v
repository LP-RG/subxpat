module abs_diff_i848_o424(a,b,r);
input [423:0] a,b;
output [423:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
