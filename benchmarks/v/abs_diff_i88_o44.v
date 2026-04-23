module abs_diff_i88_o44(a,b,r);
input [43:0] a,b;
output [43:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
