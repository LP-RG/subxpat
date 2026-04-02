module abs_diff_i776_o388(a,b,r);
input [387:0] a,b;
output [387:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
