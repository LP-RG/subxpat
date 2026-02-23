module abs_diff_i532_o266(a,b,r);
input [265:0] a,b;
output [265:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
